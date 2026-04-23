import logging
import os
from app.aws import get_ec2_ctrl, get_ecs_ctrl, get_eks_ctrl

logger = logging.getLogger(__name__)


class AWSScalingExecutor:

    def execute(self, decision: dict, creds: dict = None) -> dict:
        action        = decision.get("action")
        resource_type = decision.get("resource_type")
        target        = decision.get("target", {})
        params        = decision.get("params", {})

        logger.info(f"Executing AWS action: {action} on {resource_type} → {target}")

        try:
            if resource_type == "ec2":
                return self._handle_ec2(action, target, params, creds)
            elif resource_type == "ecs":
                return self._handle_ecs(action, target, params, creds)
            elif resource_type == "eks":
                return self._handle_eks(action, target, params, creds)
            else:
                return {"success": False, "error": f"Unknown resource_type: {resource_type}"}
        except Exception as e:
            logger.error(f"AWS execution failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _handle_ec2(self, action: str, target: dict, params: dict, creds: dict = None) -> dict:
        ec2 = get_ec2_ctrl(creds)
        asg_name = target.get("asg_name")
        if action == "scale_up":
            result = ec2.scale_up(asg_name, params.get("increment", 1))
        elif action == "scale_down":
            result = ec2.scale_down(asg_name, params.get("decrement", 1))
        elif action == "terminate_idle":
            result = ec2.terminate_idle_instances(asg_name, params.get("cpu_threshold", 5.0))
        elif action == "change_instance_type":
            result = ec2.change_instance_type(target["instance_id"], params["new_type"])
        elif action == "maintain":
            result = {"action": "maintain", "resource_type": "ec2"}
        else:
            return {"success": False, "error": f"Unknown EC2 action: {action}"}
        return {"success": True, "resource_type": "ec2", **result}

    def _handle_ecs(self, action: str, target: dict, params: dict, creds: dict = None) -> dict:
        ecs = get_ecs_ctrl(creds)
        cluster = target["cluster"]
        service = target["service"]
        if action == "scale_up":
            result = ecs.scale_up(cluster, service, params.get("increment", 1))
        elif action == "scale_down":
            result = ecs.scale_down(cluster, service, params.get("decrement", 1))
        elif action == "maintain":
            result = {"action": "maintain", "resource_type": "ecs"}
        else:
            return {"success": False, "error": f"Unknown ECS action: {action}"}
        return {"success": True, "resource_type": "ecs", **result}

    def _handle_eks(self, action: str, target: dict, params: dict, creds: dict = None) -> dict:
        eks = get_eks_ctrl(creds)
        cluster   = target["cluster"]
        nodegroup = target["nodegroup"]
        if action == "scale_up":
            result = eks.scale_up(cluster, nodegroup, params.get("increment", 1))
        elif action == "scale_down":
            result = eks.scale_down(cluster, nodegroup, params.get("decrement", 1))
        elif action == "maintain":
            result = {"action": "maintain", "resource_type": "eks"}
        else:
            return {"success": False, "error": f"Unknown EKS action: {action}"}
        return {"success": True, "resource_type": "eks", **result}


aws_executor = AWSScalingExecutor()