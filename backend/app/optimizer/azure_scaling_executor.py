import logging
import os
from app.azure import vmss_ctrl, aci_ctrl

logger = logging.getLogger(__name__)


class AzureScalingExecutor:
    """
    Translates RL agent decisions into Azure API calls.
    Exactly mirrors AWSScalingExecutor in structure so your
    RL environment can swap between them via AZURE_MODE env var.

    Decision dict format:
      action:        "scale_up" | "scale_down" | "terminate_idle"
                     | "change_vm_size" | "maintain"
      resource_type: "vmss" | "aci"
      target:        dict with resource identifiers
      params:        dict with action-specific values
    """

    def execute(self, decision: dict) -> dict:
        action        = decision.get("action")
        resource_type = decision.get("resource_type")
        target        = decision.get("target", {})
        params        = decision.get("params", {})

        logger.info(f"Azure action: {action} on {resource_type} → {target}")

        try:
            if resource_type == "vmss":
                return self._handle_vmss(action, target, params)
            elif resource_type == "aci":
                return self._handle_aci(action, target, params)
            else:
                return {"success": False, "error": f"Unknown resource_type: {resource_type}"}
        except Exception as e:
            logger.error(f"Azure execution failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _handle_vmss(self, action: str, target: dict, params: dict) -> dict:
        """
        target: {"vmss_name": "nimbusopt-vmss"}
        params: {"increment": 1} | {"new_size": "Standard_B2s"}
        """
        vmss_name = target.get("vmss_name",
                                os.getenv("AZURE_VMSS_NAME", "nimbusopt-vmss"))

        if action == "scale_up":
            result = vmss_ctrl.scale_up(vmss_name, params.get("increment", 1))
        elif action == "scale_down":
            result = vmss_ctrl.scale_down(vmss_name, params.get("decrement", 1))
        elif action == "terminate_idle":
            result = vmss_ctrl.terminate_idle_instances(
                vmss_name, params.get("cpu_threshold", 5.0)
            )
        elif action == "change_vm_size":
            result = vmss_ctrl.change_vm_size(vmss_name, params["new_size"])
        elif action == "maintain":
            result = {"action": "maintain", "resource_type": "vmss"}
        else:
            return {"success": False, "error": f"Unknown VMSS action: {action}"}

        return {"success": True, "resource_type": "vmss", **result}

    def _handle_aci(self, action: str, target: dict, params: dict) -> dict:
        """
        target: {} (ACI controller uses env vars for resource group)
        params: {"increment": 1} | {"image": "nginx:latest", "cpu": 0.5}
        """
        if action == "scale_up":
            result = aci_ctrl.scale_up(
                increment=params.get("increment", 1),
                image=params.get("image", "nginx:latest"),
                cpu=params.get("cpu", 0.5),
                memory=params.get("memory", 0.5)
            )
        elif action == "scale_down":
            result = aci_ctrl.scale_down(params.get("decrement", 1))
        elif action == "maintain":
            result = {"action": "maintain", "resource_type": "aci"}
        else:
            return {"success": False, "error": f"Unknown ACI action: {action}"}

        return {"success": True, "resource_type": "aci", **result}


# Singleton
azure_executor = AzureScalingExecutor()