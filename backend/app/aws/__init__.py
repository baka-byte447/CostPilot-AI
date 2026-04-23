import os
import logging
import boto3
from typing import Optional

from .mock_aws import (
    MockEC2Controller,
    MockECSController,
    MockEKSController,
    MockCostExplorer,
)

logger = logging.getLogger(__name__)


def _make_session(creds: Optional[dict] = None):
    if creds:
        return boto3.Session(
            aws_access_key_id=creds.get("access_key_id"),
            aws_secret_access_key=creds.get("secret_access_key"),
            region_name=creds.get("region", "us-east-1"),
        )
    return boto3.Session(
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
        region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
    )


def get_ec2_ctrl(creds: Optional[dict] = None):
    return MockEC2Controller()


def get_ecs_ctrl(creds: Optional[dict] = None):
    return MockECSController()


def get_eks_ctrl(creds: Optional[dict] = None):
    return MockEKSController()


def get_cost_explorer(creds: Optional[dict] = None):
    return MockCostExplorer()