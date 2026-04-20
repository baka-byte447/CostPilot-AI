import os
import logging

logger = logging.getLogger(__name__)

from .ec2_controller import EC2Controller
from .ecs_controller import ECSController
from .eks_controller import EKSController
from .cost_explorer import CostExplorer

def get_ec2_ctrl():
    return EC2Controller()

def get_ecs_ctrl():
    return ECSController()

def get_eks_ctrl():
    return EKSController()

def get_cost_explorer():
    return CostExplorer()