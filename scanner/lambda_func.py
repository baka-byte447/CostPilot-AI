import boto3
import logging
from datetime import datetime, timezone, timedelta
from config import AWS_REGION

logger = logging.getLogger(__name__)

def scan_lambda_waste(region=None):
    if not region:
        region = AWS_REGION
        
    findings = []
    try:
        client = boto3.client('lambda', region_name=region)
        cw = boto3.client('cloudwatch', region_name=region)
        
        paginator = client.get_paginator('list_functions')
        for page in paginator.paginate():
            for func in page['Functions']:
                func_name = func['FunctionName']
                
                # Check invocations in the last 90 days
                end_time = datetime.now(timezone.utc)
                start_time = end_time - timedelta(days=90)
                
                try:
                    metrics = cw.get_metric_statistics(
                        Namespace='AWS/Lambda',
                        MetricName='Invocations',
                        Dimensions=[{'Name': 'FunctionName', 'Value': func_name}],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=90*24*3600, # Single period for 90 days
                        Statistics=['Sum']
                    )
                    
                    datapoints = metrics.get('Datapoints', [])
                    total_invocations = datapoints[0]['Sum'] if datapoints else 0
                    
                    if total_invocations == 0:
                        findings.append({
                            "type": "Lambda Function",
                            "id": func_name,
                            "detail": "0 invocations in 90 days",
                            "waste_usd": 0.00,  # Lambdas don't cost money when not running, but take up limits
                            "region": region
                        })

                except Exception as e:
                    logger.warning(f"Could not get metrics for Lambda {func_name}: {e}")
                    
    except Exception as e:
        logger.error(f"Error scanning Lambda: {e}")
        
    return findings
