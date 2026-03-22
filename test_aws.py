
import os
from dotenv import load_dotenv
import boto3

load_dotenv()

session = boto3.Session(
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1")
)

# Test 1: Can we reach AWS at all?
try:
    sts = session.client("sts")
    identity = sts.get_caller_identity()
    print("✓ Credentials valid")
    print(f"  Account : {identity['Account']}")
    print(f"  User ARN: {identity['Arn']}")
except Exception as e:
    print(f"✗ Credential check failed: {e}")
    exit(1)

# Test 2: EC2 / ASG access
try:
    asg = session.client("autoscaling")
    resp = asg.describe_auto_scaling_groups()
    groups = resp.get("AutoScalingGroups", [])
    print(f"✓ EC2/ASG access OK — found {len(groups)} ASG(s)")
    for g in groups:
        print(f"  - {g['AutoScalingGroupName']} (desired={g['DesiredCapacity']})")
except Exception as e:
    print(f"✗ EC2/ASG access failed: {e}")

# Test 3: ECS access
try:
    ecs = session.client("ecs")
    resp = ecs.list_clusters()
    clusters = resp.get("clusterArns", [])
    print(f"✓ ECS access OK — found {len(clusters)} cluster(s)")
    for c in clusters:
        print(f"  - {c}")
except Exception as e:
    print(f"✗ ECS access failed: {e}")

# Test 4: EKS access
try:
    eks = session.client("eks")
    resp = eks.list_clusters()
    clusters = resp.get("clusters", [])
    print(f"✓ EKS access OK — found {len(clusters)} cluster(s)")
    for c in clusters:
        print(f"  - {c}")
except Exception as e:
    print(f"✗ EKS access failed: {e}")

# Test 5: Cost Explorer access
try:
    ce = session.client("ce", region_name="us-east-1")
    from datetime import datetime, timedelta
    today = datetime.utcnow().date()
    start = (today.replace(day=1)).strftime("%Y-%m-%d")
    end   = today.strftime("%Y-%m-%d")
    resp = ce.get_cost_and_usage(
        TimePeriod={"Start": start, "End": end},
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"]
    )
    amount = resp["ResultsByTime"][0]["Total"]["UnblendedCost"]["Amount"]
    print(f"✓ Cost Explorer OK — MTD spend: ${float(amount):.2f}")
except Exception as e:
    print(f"✗ Cost Explorer failed: {e}")