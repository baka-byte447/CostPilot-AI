import boto3
import os

def get_cost_client():
    return boto3.client(
        "ce",
        region_name="us-east-1"
    )

def get_ec2_client():
    return boto3.client(
        "ec2",
        region_name="us-east-1"
    )

    