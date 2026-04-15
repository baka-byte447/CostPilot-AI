
import boto3
import os
import json
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

ENDPOINT = os.getenv("AWS_ENDPOINT_URL", "http://localhost:4566")
REGION   = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

def client(service):
    return boto3.client(
        service,
        endpoint_url=ENDPOINT,
        region_name=REGION,
        aws_access_key_id="test",
        aws_secret_access_key="test"
    )


def seed_ecs():
    ecs = client("ecs")
    ecs.create_cluster(clusterName="nimbusopt-cluster")
    log.info(" ECS cluster created: nimbusopt-cluster")
    ecs.register_task_definition(
        family="nimbusopt-task",
        networkMode="bridge",
        containerDefinitions=[{
            "name": "app",
            "image": "nginx:latest",
            "cpu": 256,
            "memory": 512,
            "essential": True,
            "portMappings": [{"containerPort": 80, "hostPort": 80}]
        }],
        requiresCompatibilities=["EC2"],
        cpu="256",
        memory="512"
    )
    log.info(" ECS task definition registered: nimbusopt-task")

    # Create service
    ecs.create_service(
        cluster="nimbusopt-cluster",
        serviceName="nimbusopt-service",
        taskDefinition="nimbusopt-task",
        desiredCount=2,
        launchType="EC2"
    )
    log.info(" ECS service created: nimbusopt-service (desired=2)")


def seed_ec2_asg():
    ec2 = client("ec2")
    asg = client("autoscaling")

    lt = ec2.create_launch_template(
        LaunchTemplateName="nimbusopt-lt",
        LaunchTemplateData={
            "ImageId": "ami-0abcdef1234567890",
            "InstanceType": "t3.micro",
        }
    )
    lt_id = lt["LaunchTemplate"]["LaunchTemplateId"]
    log.info(f" Launch template created: {lt_id}")

    asg.create_auto_scaling_group(
        AutoScalingGroupName="nimbusopt-asg",
        LaunchTemplate={"LaunchTemplateId": lt_id, "Version": "$Latest"},
        MinSize=1,
        MaxSize=6,
        DesiredCapacity=2,
        AvailabilityZones=["us-east-1a"]
    )
    log.info(" ASG created: nimbusopt-asg (desired=2, min=1, max=6)")


def seed_eks():
    eks = client("eks")

    eks.create_cluster(
        name="nimbusopt-eks",
        version="1.28",
        roleArn="arn:aws:iam::000000000000:role/eks-role", ####
        resourcesVpcConfig={
            "subnetIds": ["subnet-12345"],
            "securityGroupIds": ["sg-12345"]
        }
    )
    log.info(" EKS cluster created: nimbusopt-eks")

    eks.create_nodegroup(
        clusterName="nimbusopt-eks",
        nodegroupName="nimbusopt-nodegroup",
        scalingConfig={"minSize": 1, "maxSize": 5, "desiredSize": 2},
        subnets=["subnet-12345"],
        nodeRole="arn:aws:iam::000000000000:role/node-role",  #fake
        instanceTypes=["t3.medium"]
    )
    log.info("EKS nodegroup created: nimbusopt-nodegroup (desired=2)")


def seed_cloudwatch():
    cw = client("cloudwatch")
    from datetime import datetime, timezone, timedelta

    cw.put_metric_data(
        Namespace="AWS/EC2",
        MetricData=[{
            "MetricName": "CPUUtilization",
            "Dimensions": [{"Name": "InstanceId", "Value": "i-localstack001"}],
            "Timestamp": datetime.now(timezone.utc) - timedelta(minutes=5),
            "Value": 3.2,
            "Unit": "Percent"
        }]
    )
    log.info("CloudWatch CPU metric seeded for i-localstack001 (3.2% — idle)")


if __name__ == "__main__":
    log.info("Seeding LocalStack with fake AWS resources...\n")
    try:
        seed_ecs()
        seed_ec2_asg()
        seed_eks()
        seed_cloudwatch()
        log.info("\nAll resources seeded successfully.")
        log.info("  ECS  → cluster: nimbusopt-cluster  service: nimbusopt-service")
        log.info("  EC2  → asg: nimbusopt-asg")
        log.info("  EKS  → cluster: nimbusopt-eks  nodegroup: nimbusopt-nodegroup")
    except Exception as e:
        log.error(f"Seeding failed: {e}")
        raise