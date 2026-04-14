import boto3
import os
from dotenv import load_dotenv

load_dotenv()

class AWSClientManager:
    def __init__(self):
        self.region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        self.endpoint_url = os.getenv("AWS_ENDPOINT_URL", None)

        self.session = boto3.Session(
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
            region_name=self.region
        )

    def _client(self, service: str, region: str = None):
        return self.session.client(
            service,
            region_name=region or self.region,
            endpoint_url=self.endpoint_url
        )

    def ec2(self):         return self._client("ec2")
    def autoscaling(self): return self._client("autoscaling")
    def ecs(self):         return self._client("ecs")
    def eks(self):         return self._client("eks")
    def cloudwatch(self):  return self._client("cloudwatch")
    def sts(self):         return self._client("sts")
    def cost_explorer(self):
        return self._client("ce", region="us-east-1")

aws = AWSClientManager()


