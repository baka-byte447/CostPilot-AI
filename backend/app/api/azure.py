from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/azure", tags=["azure"])


@router.get("/vmss")
def list_vmss():
    try:
        from app.azure import get_vmss_ctrl
        return get_vmss_ctrl().list_vmss()
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/vmss/{vmss_name}")
def get_vmss(vmss_name: str):
    try:
        from app.azure import get_vmss_ctrl
        return get_vmss_ctrl().get_vmss_info(vmss_name)
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/aci")
def list_aci_groups():
    try:
        from app.azure import get_aci_ctrl
        return get_aci_ctrl().list_groups()
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/aci/info")
def get_aci_info():
    try:
        from app.azure import get_aci_ctrl
        return get_aci_ctrl().get_info()
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/cost/current-month")
def current_month_cost():
    try:
        from app.azure import get_azure_cost
        return get_azure_cost().get_current_month_cost()
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/cost/by-service")
def cost_by_service(days: int = 7):
    try:
        from app.azure import get_azure_cost
        return get_azure_cost().get_cost_by_service(days)
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


class AzureScalingAction(BaseModel):
    action: str
    resource_type: str
    target: dict = {}
    params: dict = {}


@router.post("/scale")
def execute_azure_scaling(body: AzureScalingAction):
    try:
        from app.optimizer.azure_scaling_executor import azure_executor
        result = azure_executor.execute(body.dict())
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))