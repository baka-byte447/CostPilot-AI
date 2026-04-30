import boto3
import logging
from config import AWS_REGION

logger = logging.getLogger(__name__)

def scan_s3_waste():
    findings = []
    try:
        s3 = boto3.client('s3', region_name=AWS_REGION)
        # S3 lists all buckets globally, but we'll scan them here
        response = s3.list_buckets()
        buckets = response.get('Buckets', [])
        
        for bucket in buckets:
            bucket_name = bucket['Name']
            
            # 1. Check for empty buckets
            try:
                objects = s3.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
                is_empty = 'Contents' not in objects
                if is_empty:
                    findings.append({
                        "type": "S3 Bucket",
                        "id": bucket_name,
                        "detail": "Empty bucket",
                        "waste_usd": 0.00,  # Empty buckets are mostly free but clutter
                        "region": "global"
                    })
                    continue
            except Exception as e:
                logger.warning(f"Could not list objects in S3 bucket {bucket_name}: {e}")
                
            # 2. Check for incomplete multipart uploads (hidden waste!)
            try:
                multiparts = s3.list_multipart_uploads(Bucket=bucket_name)
                uploads = multiparts.get('Uploads', [])
                if uploads:
                    # Estimate cost: Usually costs standard S3 storage rates per GB, we'll estimate a small flat fee for the alert
                    findings.append({
                        "type": "S3 Multipart",
                        "id": f"{bucket_name} (Uploads)",
                        "detail": f"{len(uploads)} incomplete multipart uploads",
                        "waste_usd": len(uploads) * 0.50, # Rough estimate for hidden waste
                        "region": "global"
                    })
            except Exception as e:
                logger.warning(f"Could not check multipart uploads for {bucket_name}: {e}")
                
    except Exception as e:
        logger.error(f"Error scanning S3: {e}")
        
    return findings
