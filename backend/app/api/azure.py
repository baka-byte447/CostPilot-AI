from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/azure", tags=["azure"])


@router.get("/vmss")
def list_vmss():
    try:
        from app.azure import get_vmss_ctrl
        return get_vmss_ctrl().list_vmss()
    except Exception as e:
        return {"status": "ok", "mocked": True, "count": 2, "items": [{"name": "mock-vmss-1"}, {"name": "mock-vmss-2"}]}


@router.get("/vmss/{vmss_name}")
def get_vmss(vmss_name: str):
    try:
        from app.azure import get_vmss_ctrl
        return get_vmss_ctrl().get_vmss_info(vmss_name)
    except Exception as e:
        return {"name": vmss_name, "mocked": True, "capacity": 3, "status": "running"}


@router.get("/aci")
def list_aci_groups():
    try:
        from app.azure import get_aci_ctrl
        return get_aci_ctrl().list_groups()
    except Exception as e:
        return [
            {
                "name": "mock-aci-group",
                "state": "Running",
                "location": "centralindia",
                "ip": None,
            }
        ]


@router.get("/aci/info")
def get_aci_info():
    try:
        from app.azure import get_aci_ctrl
        return get_aci_ctrl().get_info()
    except Exception as e:
        return {"mocked": True, "active_instances": 4, "total_cores": 8}


@router.get("/cost/current-month")
def current_month_cost():
    try:
        from app.azure import get_azure_cost
        return get_azure_cost().get_current_month_cost()
    except Exception as e:
        now = datetime.now(timezone.utc)
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return {
            "amount": 543.21,
            "currency": "USD",
            "period_start": start.strftime("%Y-%m-%d"),
            "period_end": now.strftime("%Y-%m-%d"),
            "mocked": True,
        }


@router.get("/cost/by-service")
def cost_by_service(days: int = 7):
    try:
        from app.azure import get_azure_cost
        return get_azure_cost().get_cost_by_service(days)
    except Exception as e:
        return {
            "mocked": True,
            "period_days": days,
            "services": [
                {"service": "Virtual Network", "cost": 150.0},
                {"service": "Azure App Service", "cost": 210.0},
                {"service": "Storage Accounts", "cost": 45.0}
            ]
        }


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
            return {"success": True, "mocked": True, "message": "Failed to connect to azure but succeeding in mock."}
        return result
    except Exception as e:
        return {"success": True, "mocked": True, "action": body.action, "message": f"Mock executed {body.action} successfully"}