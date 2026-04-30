import boto3
import logging
from config import AWS_REGION, STOPPED_EC2_EBS_ESTIMATE, EC2_CPU_THRESHOLD
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


def scan_stopped_ec2(region=None):
    """Find EC2 instances that are in a stopped state. Uses pagination."""
    if not region:
        region = AWS_REGION
        
    findings = []
    try:
        ec2 = boto3.client("ec2", region_name=region)
        paginator = ec2.get_paginator("describe_instances")
        page_iterator = paginator.paginate(
            Filters=[{"Name": "instance-state-name", "Values": ["stopped"]}]
        )

        for page in page_iterator:
            for reservation in page["Reservations"]:
                for instance in reservation["Instances"]:
                    instance_id = instance["InstanceId"]
                    instance_type = instance["InstanceType"]

                    # Get name tag if it exists
                    name = "unnamed"
                    for tag in instance.get("Tags", []):
                        if tag["Key"] == "Name":
                            name = tag["Value"]
                            break

                    findings.append({
                        "type": "Stopped EC2",
                        "id": instance_id,
                        "detail": f"Stopped instance '{name}' ({instance_type})",
                        "waste_usd": STOPPED_EC2_EBS_ESTIMATE,
                        "region": region
                    })


        logger.info(f"EC2 scan complete — {len(findings)} stopped instances found.")
    except Exception as e:
        logger.error(f"EC2 scan failed: {e}")

    return findings


def scan_idle_ec2(region=None):
    """Find running EC2 instances with low CPU utilization using CloudWatch."""
    if not region:
        region = AWS_REGION
        
    findings = []
    try:
        ec2 = boto3.client("ec2", region_name=region)
        cw = boto3.client("cloudwatch", region_name=region)
        
        # Get all running instances
        instances = ec2.describe_instances(
            Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
        )
        
        for reservation in instances["Reservations"]:
            for instance in reservation["Instances"]:
                instance_id = instance["InstanceId"]
                instance_type = instance["InstanceType"]
                
                # Only consider instances running for more than 24 hours to avoid false positives on new instances
                launch_time = instance.get("LaunchTime")
                if launch_time:
                    age = datetime.now(timezone.utc) - launch_time
                    if age.total_seconds() < 86400: # 24 hours
                        continue

                # Fetch CPU utilization for the last 7 days
                end_time = datetime.now(timezone.utc)
                start_time = end_time - timedelta(days=7)
                
                metrics = cw.get_metric_statistics(
                    Namespace="AWS/EC2",
                    MetricName="CPUUtilization",
                    Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=86400, # Daily average
                    Statistics=["Average"]
                )
                
                datapoints = metrics.get("Datapoints", [])
                if not datapoints or len(datapoints) < 3: # Require at least 3 days of data
                    continue
                    
                avg_cpu = sum(d["Average"] for d in datapoints) / len(datapoints)
                
                if avg_cpu < EC2_CPU_THRESHOLD:
                    name = "unnamed"
                    for tag in instance.get("Tags", []):
                        if tag["Key"] == "Name":
                            name = tag["Value"]
                            break
                            
                    findings.append({
                        "type": "Idle EC2",
                        "id": instance_id,
                        "detail": f"Running but idle '{name}' (Avg CPU: {avg_cpu:.1f}% over {len(datapoints)} days)",
                        "waste_usd": 15.0,  # Generic estimate
                        "region": region
                    })
                    
        logger.info(f"EC2 Idle scan complete — {len(findings)} idle instances found.")
    except Exception as e:
        logger.error(f"EC2 Idle scan failed: {e}")
        
    return findings
