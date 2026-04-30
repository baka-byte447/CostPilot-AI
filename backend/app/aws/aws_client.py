import logging
import os
import uuid
from functools import lru_cache
from typing import Optional

import boto3
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


def _build_default_session(region: str, endpoint_url: Optional[str]) -> boto3.Session:
    if endpoint_url:
        return boto3.Session(
            aws_access_key_id="test",
            aws_secret_access_key="test",
            region_name=region,
        )
    return boto3.Session(region_name=region)


def assume_role_session(
    role_arn: str,
    external_id: Optional[str] = None,
    region: Optional[str] = None,
    endpoint_url: Optional[str] = None,
    duration_seconds: int = 3600,
    session_name: Optional[str] = None,
) -> boto3.Session:
    region = region or os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    base_session = _build_default_session(region, endpoint_url)
    sts_client = base_session.client(
        "sts",
        region_name=region,
        endpoint_url=endpoint_url,
    )

    if not session_name:
        session_name = f"costpilot-{uuid.uuid4().hex[:12]}"

    params = {
        "RoleArn": role_arn,
        "RoleSessionName": session_name,
        "DurationSeconds": duration_seconds,
    }
    if external_id:
        params["ExternalId"] = external_id

    response = sts_client.assume_role(**params)
    creds = response["Credentials"]
    return boto3.Session(
        aws_access_key_id=creds["AccessKeyId"],
        aws_secret_access_key=creds["SecretAccessKey"],
        aws_session_token=creds["SessionToken"],
        region_name=region,
    )


class AWSClientManager:
    def __init__(
        self,
        session: Optional[boto3.Session] = None,
        region: Optional[str] = None,
        endpoint_url: Optional[str] = None,
    ):
        self.region = region or os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        self.endpoint_url = (
            endpoint_url if endpoint_url is not None else os.getenv("AWS_ENDPOINT_URL", None)
        )
        self.session = session or _build_default_session(self.region, self.endpoint_url)

    @classmethod
    def from_assumed_role(
        cls,
        role_arn: str,
        external_id: Optional[str] = None,
        region: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        duration_seconds: int = 3600,
        session_name: Optional[str] = None,
    ) -> "AWSClientManager":
        if endpoint_url is None:
            endpoint_url = os.getenv("AWS_ENDPOINT_URL", None)
        session = assume_role_session(
            role_arn=role_arn,
            external_id=external_id,
            region=region,
            endpoint_url=endpoint_url,
            duration_seconds=duration_seconds,
            session_name=session_name,
        )
        return cls(session=session, region=region, endpoint_url=endpoint_url)

    def _client(self, service: str, region: Optional[str] = None):
        return self.session.client(
            service,
            region_name=region or self.region,
            endpoint_url=self.endpoint_url,
        )

    def ec2(self):
        return self._client("ec2")

    def autoscaling(self):
        return self._client("autoscaling")

    def ecs(self):
        return self._client("ecs")

    def eks(self):
        return self._client("eks")

    def cloudwatch(self):
        return self._client("cloudwatch")

    def sts(self):
        return self._client("sts")

    def cost_explorer(self):
        return self._client("ce", region="us-east-1")


@lru_cache(maxsize=1)
def get_default_aws_manager() -> AWSClientManager:
    return AWSClientManager()


aws = get_default_aws_manager()


