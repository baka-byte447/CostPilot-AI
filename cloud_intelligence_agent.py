import boto3
import json
import logging
import smtplib
import time
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] CloudAgent: %(message)s")
logger = logging.getLogger(__name__)

class CloudIntelligenceAgent:
    def __init__(self, aws_key, aws_secret, aws_region, aws_regions, 
                 ec2_cpu_threshold=5.0, snapshot_age_days=30, budget_threshold=50.0,
                 smtp_host=None, smtp_port=587, smtp_user=None, smtp_password=None, 
                 smtp_from=None, smtp_to=None):
        self.aws_key = aws_key
        self.aws_secret = aws_secret
        self.default_region = aws_region
        self.scan_regions = [r.strip() for r in aws_regions.split(",") if r.strip()]
        self.ec2_cpu_threshold = float(ec2_cpu_threshold)
        self.snapshot_age_days = int(snapshot_age_days)
        self.budget_threshold = float(budget_threshold)
        
        # SMTP Config
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.smtp_from = smtp_from
        self.smtp_to = smtp_to

        # Boto3 Config with Retries
        self.boto_config = Config(
            retries={'max_attempts': 3, 'mode': 'standard'},
            region_name=self.default_region
        )

    def _get_session(self, region):
        return boto3.Session(
            aws_access_key_id=self.aws_key,
            aws_secret_access_key=self.aws_secret,
            region_name=region
        )

    def connect(self):
        """Validate credentials (STS GetCallerIdentity)."""
        logger.info("Validating AWS credentials...")
        try:
            session = self._get_session(self.default_region)
            sts = session.client('sts', config=self.boto_config)
            identity = sts.get_caller_identity()
            logger.info(f"Connection established for Account: {identity['Account']}")
            return identity['Account']
        except Exception as e:
            logger.error(f"Credential validation failed: {e}")
            return None

    def scan_ec2_waste(self, session, region):
        findings = []
        ec2 = session.client('ec2', config=self.boto_config)
        cw = session.client('cloudwatch', config=self.boto_config)
        
        try:
            # 1. Idle EC2 (CPU < threshold over 14 days)
            instances = ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
            for res in instances.get('Reservations', []):
                for inst in res.get('Instances', []):
                    iid = inst['InstanceId']
                    metrics = cw.get_metric_statistics(
                        Namespace='AWS/EC2', MetricName='CPUUtilization',
                        Dimensions=[{'Name': 'InstanceId', 'Value': iid}],
                        StartTime=datetime.now(timezone.utc) - timedelta(days=14),
                        EndTime=datetime.now(timezone.utc),
                        Period=86400, Statistics=['Average']
                    )
                    points = metrics.get('Datapoints', [])
                    if points:
                        avg_cpu = sum(p['Average'] for p in points) / len(points)
                        if avg_cpu < self.ec2_cpu_threshold:
                            findings.append({
                                "resource_id": iid, "resource_type": "ec2", "region": region,
                                "waste_category": "oversized", "priority": "high",
                                "estimated_monthly_cost_usd": 25.0, # Approximate base
                                "recommendation": f"Downsize or terminate. Avg CPU {avg_cpu:.1f}% is below {self.ec2_cpu_threshold}% threshold.",
                                "auto_remediable": False
                            })

            # 2. Stopped Instances > 7 days
            stopped = ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['stopped']}])
            for res in stopped.get('Reservations', []):
                for inst in res.get('Instances', []):
                    # Check transition time if available via tags or just flag all stopped
                    findings.append({
                        "resource_id": inst['InstanceId'], "resource_type": "ec2", "region": region,
                        "waste_category": "idle", "priority": "medium",
                        "estimated_monthly_cost_usd": 5.0,
                        "recommendation": "Instance is stopped but incurring EBS storage costs. Terminate if no longer needed.",
                        "auto_remediable": True
                    })

            # 3. Unattached EIPs
            eips = ec2.describe_addresses()
            for addr in eips.get('Addresses', []):
                if 'InstanceId' not in addr and 'NetworkInterfaceId' not in addr:
                    findings.append({
                        "resource_id": addr.get('AllocationId', addr['PublicIp']), "resource_type": "ec2", "region": region,
                        "waste_category": "orphaned", "priority": "medium",
                        "estimated_monthly_cost_usd": 3.60,
                        "recommendation": "Release unattached Elastic IP address.",
                        "auto_remediable": True
                    })

        except ClientError as e:
            logger.warning(f"EC2 Scan failed in {region}: {e}")
        return findings

    def scan_ebs_waste(self, session, region):
        findings = []
        ec2 = session.client('ec2', config=self.boto_config)
        try:
            # 1. Unattached Volumes
            vols = ec2.describe_volumes(Filters=[{'Name': 'status', 'Values': ['available']}])
            for vol in vols.get('Volumes', []):
                findings.append({
                    "resource_id": vol['VolumeId'], "resource_type": "ebs", "region": region,
                    "waste_category": "orphaned", "priority": "high",
                    "estimated_monthly_cost_usd": vol['Size'] * 0.1,
                    "recommendation": "Delete unattached EBS volume.",
                    "auto_remediable": True
                })

            # 2. Old Snapshots (no AMI)
            snaps = ec2.describe_snapshots(OwnerIds=['self'])
            cutoff = datetime.now(timezone.utc) - timedelta(days=self.snapshot_age_days)
            for snap in snaps.get('Snapshots', []):
                if snap['StartTime'] < cutoff:
                    findings.append({
                        "resource_id": snap['SnapshotId'], "resource_type": "ebs", "region": region,
                        "waste_category": "stale", "priority": "low",
                        "estimated_monthly_cost_usd": snap.get('VolumeSize', 0) * 0.05,
                        "recommendation": f"Snapshot is older than {self.snapshot_age_days} days. Delete if not required for backup.",
                        "auto_remediable": True
                    })
        except ClientError as e:
            logger.warning(f"EBS Scan failed in {region}: {e}")
        return findings

    def scan_s3_waste(self, session):
        findings = []
        s3 = session.client('s3', config=self.boto_config)
        cw = session.client('cloudwatch', region_name='us-east-1') # Metrics are in us-east-1
        try:
            buckets = s3.list_buckets().get('Buckets', [])
            for b in buckets:
                name = b['Name']
                # Zero Requests Check
                metrics = cw.get_metric_statistics(
                    Namespace='AWS/S3', MetricName='AllRequests',
                    Dimensions=[{'Name': 'BucketName', 'Value': name}, {'Name': 'FilterId', 'Value': 'EntireBucket'}],
                    StartTime=datetime.now(timezone.utc) - timedelta(days=30),
                    EndTime=datetime.now(timezone.utc),
                    Period=2592000, Statistics=['Sum']
                )
                if not metrics.get('Datapoints') or metrics['Datapoints'][0]['Sum'] == 0:
                    findings.append({
                        "resource_id": name, "resource_type": "s3", "region": "global",
                        "waste_category": "idle", "priority": "medium",
                        "estimated_monthly_cost_usd": 1.0, # Nominal base
                        "recommendation": "Bucket has zero requests in 30 days. Review and archive or delete.",
                        "auto_remediable": False
                    })
        except Exception as e:
            logger.warning(f"S3 Scan failed: {e}")
        return findings

    def scan_rds_waste(self, session, region):
        findings = []
        rds = session.client('rds', config=self.boto_config)
        cw = session.client('cloudwatch', config=self.boto_config)
        try:
            instances = rds.describe_db_instances().get('DBInstances', [])
            for db in instances:
                dbi = db['DBInstanceIdentifier']
                # Idle DB (0 connections in 7 days)
                metrics = cw.get_metric_statistics(
                    Namespace='AWS/RDS', MetricName='DatabaseConnections',
                    Dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': dbi}],
                    StartTime=datetime.now(timezone.utc) - timedelta(days=7),
                    EndTime=datetime.now(timezone.utc),
                    Period=604800, Statistics=['Maximum']
                )
                if not metrics.get('Datapoints') or metrics['Datapoints'][0]['Maximum'] == 0:
                    findings.append({
                        "resource_id": dbi, "resource_type": "rds", "region": region,
                        "waste_category": "idle", "priority": "critical",
                        "estimated_monthly_cost_usd": 50.0, # High base cost
                        "recommendation": "DB instance has zero connections in 7 days. Snapshot and delete.",
                        "auto_remediable": False
                    })
                # Security: Publicly Accessible
                if db.get('PubliclyAccessible') and not db.get('StorageEncrypted'):
                    findings.append({
                        "resource_id": dbi, "resource_type": "rds", "region": region,
                        "waste_category": "insecure", "priority": "critical",
                        "estimated_monthly_cost_usd": 0.0,
                        "recommendation": "DB is public and unencrypted. Restrict access and enable encryption.",
                        "auto_remediable": False
                    })
        except Exception as e:
            logger.warning(f"RDS Scan failed in {region}: {e}")
        return findings

    def scan_lambda_waste(self, session, region):
        findings = []
        lmb = session.client('lambda', config=self.boto_config)
        cw = session.client('cloudwatch', config=self.boto_config)
        try:
            funcs = lmb.list_functions().get('Functions', [])
            for f in funcs:
                name = f['FunctionName']
                # Not invoked in 30 days
                metrics = cw.get_metric_statistics(
                    Namespace='AWS/Lambda', MetricName='Invocations',
                    Dimensions=[{'Name': 'FunctionName', 'Value': name}],
                    StartTime=datetime.now(timezone.utc) - timedelta(days=30),
                    EndTime=datetime.now(timezone.utc),
                    Period=2592000, Statistics=['Sum']
                )
                if not metrics.get('Datapoints') or metrics['Datapoints'][0]['Sum'] == 0:
                    findings.append({
                        "resource_id": name, "resource_type": "lambda", "region": region,
                        "waste_category": "idle", "priority": "low",
                        "estimated_monthly_cost_usd": 0.0,
                        "recommendation": "Function has not been invoked in 30 days.",
                        "auto_remediable": True
                    })
        except Exception as e:
            logger.warning(f"Lambda Scan failed in {region}: {e}")
        return findings

    def run_full_scan(self):
        account_id = self.connect()
        if not account_id:
            return {"error": "Authentication failed"}

        all_findings = []
        
        # Scan Global S3 once
        global_session = self._get_session(self.default_region)
        all_findings.extend(self.scan_s3_waste(global_session))

        # Scan across regions
        for region in self.scan_regions:
            logger.info(f"Scanning region: {region}...")
            try:
                session = self._get_session(region)
                all_findings.extend(self.scan_ec2_waste(session, region))
                all_findings.extend(self.scan_ebs_waste(session, region))
                all_findings.extend(self.scan_rds_waste(session, region))
                all_findings.extend(self.scan_lambda_waste(session, region))
            except Exception as e:
                logger.warning(f"Skipping region {region} due to error: {e}")

        total_waste = sum(f['estimated_monthly_cost_usd'] for f in all_findings)
        
        report = {
            "scan_summary": {
                "account_id": account_id,
                "scanned_regions": self.scan_regions,
                "scan_timestamp": datetime.now(timezone.utc).isoformat(),
                "total_estimated_monthly_waste_usd": round(total_waste, 2)
            },
            "findings": all_findings,
            "budget_alert": {
                "threshold_usd": self.budget_threshold,
                "exceeded": total_waste > self.budget_threshold,
                "message": f"Waste ${total_waste:.2f} exceeds threshold ${self.budget_threshold:.2f}" if total_waste > self.budget_threshold else "Within budget"
            }
        }

        if report["budget_alert"]["exceeded"]:
            self.send_email_alert(report)

        return report

    def send_email_alert(self, report):
        if not all([self.smtp_host, self.smtp_user, self.smtp_password, self.smtp_from, self.smtp_to]):
            logger.warning("SMTP not fully configured. Skipping email alert.")
            return

        try:
            top_findings = sorted(report['findings'], key=lambda x: x['estimated_monthly_cost_usd'], reverse=True)[:5]
            
            body = f"CloudWatch Alert: AWS waste exceeded ${self.budget_threshold} this month.\n\n"
            body += f"Total Estimated Waste: ${report['scan_summary']['total_estimated_monthly_waste_usd']:.2f}\n"
            body += f"Account ID: {report['scan_summary']['account_id']}\n\n"
            body += "Top 5 Findings:\n"
            for f in top_findings:
                body += f"- [{f['resource_type'].upper()}] {f['resource_id']} ({f['region']}): ${f['estimated_monthly_cost_usd']:.2f} - {f['recommendation']}\n"
            
            body += "\nCall to Action: Log in to CostPilot-AI dashboard to remediate these resources."

            msg = MIMEText(body)
            msg['Subject'] = f"[CloudWatch Alert] AWS waste exceeded ${self.budget_threshold} this month"
            msg['From'] = self.smtp_from
            msg['To'] = self.smtp_to

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            logger.info("Alert email sent successfully.")
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")

if __name__ == "__main__":
    # Example usage / testing
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    agent = CloudIntelligenceAgent(
        aws_key=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret=os.getenv("AWS_SECRET_ACCESS_KEY"),
        aws_region=os.getenv("AWS_DEFAULT_REGION", "ap-south-1"),
        aws_regions=os.getenv("AWS_REGIONS", "ap-south-1"),
        smtp_host=os.getenv("SMTP_HOST"),
        smtp_user=os.getenv("SMTP_USER"),
        smtp_password=os.getenv("SMTP_PASSWORD"),
        smtp_from=os.getenv("ALERT_FROM"),
        smtp_to=os.getenv("ALERT_TO")
    )
    
    print(json.dumps(agent.run_full_scan(), indent=2))
