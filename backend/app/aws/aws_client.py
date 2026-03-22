import boto3
import os
from dotenv import load_dotenv

load_dotenv()

class AWSClientManager:
    def __init__ (self):
        self.region = os.getenv("AWS_DEFAULT_REGION","us-east-1")
        self.session= boto3.Session(aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"), aws_secret_accesss_key = os.getenv("AWS_SECRET_ACCESS_KEY"),
                                    region_name=self.region)
        
    def es2(self):
        return self.session.client("ec2")
    def autoscaling(self):
        return self.session.client("autoscaling")
    def ecs(self):
        return self.session.client("ecs")
    def eks(self):
        return self.session.client("eks")
    def cloudwatch(self):
        return self.session.client("cloudwatch")
    def cost_explorer(self):
        return self.session.client("ce", region_name="us-east-1")
    
aws = AWSClientManager()

 