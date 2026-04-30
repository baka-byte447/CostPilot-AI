import os
import logging

logger = logging.getLogger(__name__)

from .cost_explorer import CostExplorer
from .ec2_controller import EC2Controller
from .ecs_controller import ECSController
from .eks_controller import EKSController

def get_ec2_ctrl(aws_manager=None):
    return EC2Controller(aws_manager)

def get_ecs_ctrl(aws_manager=None):
    return ECSController(aws_manager)

def get_eks_ctrl(aws_manager=None):
    return EKSController(aws_manager)

def get_cost_explorer(aws_manager=None):
    return CostExplorer(aws_manager)