import os
import logging

logger = logging.getLogger(__name__)

# Use mock controllers — LocalStack free tier doesn't support
# ECS, EKS, or AutoScaling. Mock provides identical API surface.
from .mock_aws import (
    MockEC2Controller,
    MockECSController,
    MockEKSController,
    MockCostExplorer
)

def get_ec2_ctrl():
    return MockEC2Controller()

def get_ecs_ctrl():
    return MockECSController()

def get_eks_ctrl():
    return MockEKSController()

def get_cost_explorer():
    return MockCostExplorer()