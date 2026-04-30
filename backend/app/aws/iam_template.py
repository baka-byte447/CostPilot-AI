from textwrap import dedent, indent
from typing import List

READ_ONLY_ACTIONS = [
    "ce:Get*",
    "ce:List*",
    "cloudwatch:GetMetricData",
    "cloudwatch:GetMetricStatistics",
    "cloudwatch:ListMetrics",
    "ec2:Describe*",
    "autoscaling:Describe*",
    "ecs:Describe*",
    "ecs:List*",
    "eks:Describe*",
    "eks:List*",
    "pricing:GetProducts",
    "sts:GetCallerIdentity",
]

WRITE_ACTIONS = [
    "autoscaling:SetDesiredCapacity",
    "autoscaling:TerminateInstanceInAutoScalingGroup",
    "ecs:UpdateService",
    "eks:UpdateNodegroupConfig",
    "ec2:StartInstances",
    "ec2:StopInstances",
    "ec2:ModifyInstanceAttribute",
]


def _format_actions(actions: List[str], indent_size: int) -> str:
  prefix = " " * indent_size
  return "\n".join([f"{prefix}- \"{action}\"" for action in actions])


def build_role_template(
    control_account_id: str,
    external_id: str,
    role_name: str,
    allow_write: bool = False,
) -> str:
    read_only_actions = _format_actions(READ_ONLY_ACTIONS, 16)
    write_actions = _format_actions(WRITE_ACTIONS, 8)

    write_block = ""
    if allow_write:
        write_policy = dedent(
            f"""
            - PolicyName: CostPilotWrite
              PolicyDocument:
                Version: "2012-10-17"
                Statement:
                  - Effect: Allow
                    Action:
{write_actions}
                    Resource: "*"
            """
        ).rstrip()
        write_block = indent(write_policy, " " * 8)

    template = dedent(
        f"""
        AWSTemplateFormatVersion: "2010-09-09"
        Description: CostPilot cross-account access role
        Resources:
          CostPilotAccessRole:
            Type: AWS::IAM::Role
            Properties:
              RoleName: {role_name}
              AssumeRolePolicyDocument:
                Version: "2012-10-17"
                Statement:
                  - Effect: Allow
                    Principal:
                      AWS: "arn:aws:iam::{control_account_id}:root"
                    Action: "sts:AssumeRole"
                    Condition:
                      StringEquals:
                        sts:ExternalId: "{external_id}"
              Policies:
                - PolicyName: CostPilotReadOnly
                  PolicyDocument:
                    Version: "2012-10-17"
                    Statement:
                      - Effect: Allow
                        Action:
{read_only_actions}
                        Resource: "*"
        """
    ).rstrip()

    if write_block:
        template = f"{template}\n{write_block}"

    return template + "\n"
