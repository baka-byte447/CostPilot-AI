
import os
import boto3
from botocore.exceptions import BotoCoreError, ClientError

ENDPOINT = os.getenv("AWS_ENDPOINT_URL")
REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")


def make_session():
    if ENDPOINT:
        return boto3.Session(
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
            region_name=REGION
        )
    return boto3.Session(region_name=REGION)


def client(session, service, region=None):
    return session.client(service, region_name=region or REGION, endpoint_url=ENDPOINT)


def check_sts(session):
    sts = client(session, "sts")
    ident = sts.get_caller_identity()
    print(f"STS OK: {ident.get('Arn')} (acct {ident.get('Account')})")


def check_iam(session):
    iam = client(session, "iam")
    try:
        user = iam.get_user().get("User", {})
        print(f"IAM OK: {user.get('UserName')} ({user.get('Arn')})")
    except ClientError as e:
        print(f"IAM check failed: {e}")


def check_cost(session):
    if ENDPOINT:
        print("Cost Explorer skipped (AWS_ENDPOINT_URL set).")
        return
    ce = client(session, "ce", region="us-east-1")
    resp = ce.get_cost_and_usage(
        TimePeriod={"Start": "2026-04-01", "End": "2026-04-30"},
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"]
    )
    results = resp.get("ResultsByTime", [])
    amount = 0.0
    if results:
        amount = float(results[0]["Total"]["UnblendedCost"]["Amount"])
    print(f"Cost Explorer OK: ${amount:.2f} MTD")


def check_asg(session):
    asg = client(session, "autoscaling")
    resp = asg.describe_auto_scaling_groups()
    print(f"ASG OK: {len(resp.get('AutoScalingGroups', []))} group(s)")


def check_ecs(session):
    ecs = client(session, "ecs")
    clusters = ecs.list_clusters().get("clusterArns", [])
    print(f"ECS OK: {len(clusters)} cluster(s)")


def check_eks(session):
    eks = client(session, "eks")
    clusters = eks.list_clusters().get("clusters", [])
    print(f"EKS OK: {len(clusters)} cluster(s)")


def main():
    print(f"Region: {REGION}")
    print(f"Endpoint: {ENDPOINT or 'aws'}")
    session = make_session()
    creds = session.get_credentials()
    if not creds:
        print("ERROR: No AWS credentials resolved via default chain.")
        raise SystemExit(2)

    failures = 0
    checks = [check_sts, check_iam, check_cost, check_asg, check_ecs, check_eks]
    for check in checks:
        try:
            check(session)
        except (BotoCoreError, ClientError) as e:
            failures += 1
            print(f"{check.__name__} failed: {e}")

    if failures:
        print(f"Completed with {failures} failure(s)")
        raise SystemExit(1)

    print("All AWS checks passed")


if __name__ == "__main__":
    main()