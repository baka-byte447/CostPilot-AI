from fastapi import APIRouter, HTTPException
from app.azure import vmss_ctrl, aci_ctrl, azure_cost
from app.optimizer.azure_scaling_executor import azure_executor
from pydantic import BaseModel

router = APIRouter(prefix="/azure", tags=["azure"])


# ── Discovery ─────────────────────────────────────────────────────────────────

@router.get("/vmss")
def list_vmss():
    """List all VM Scale Sets in the resource group."""
    return vmss_ctrl.list_vmss()

@router.get("/vmss/{vmss_name}")
def get_vmss(vmss_name: str):
    return vmss_ctrl.get_vmss_info(vmss_name)

@router.get("/aci")
def list_aci_groups():
    """List all managed container groups."""
    return aci_ctrl.list_groups()

@router.get("/aci/info")
def get_aci_info():
    return aci_ctrl.get_info()


# ── Cost ──────────────────────────────────────────────────────────────────────

@router.get("/cost/current-month")
def current_month_cost():
    """Real Azure spend from your student credits this month."""
    return azure_cost.get_current_month_cost()

@router.get("/cost/by-service")
def cost_by_service(days: int = 7):
    return azure_cost.get_cost_by_service(days)


# ── Scaling actions ───────────────────────────────────────────────────────────

class AzureScalingAction(BaseModel):
    action: str          # scale_up | scale_down | terminate_idle | maintain
    resource_type: str   # vmss | aci
    target: dict = {}
    params: dict = {}

@router.post("/scale")
def execute_azure_scaling(body: AzureScalingAction):
    """
    Manual scaling endpoint — also used by the RL agent
    when AZURE_MODE=true.
    """
    result = azure_executor.execute(body.dict())
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result