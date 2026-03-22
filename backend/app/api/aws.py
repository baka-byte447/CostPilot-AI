from fastapi import APIRouter, HTTPException
from app.aws import ec2_ctrl, ecs_ctrl, eks_ctrl, cost_explorer
from app.optimizer.aws_scaling_executor import aws_executor
from pydantic import BaseModel

router = APIRouter(prefix="/aws", tags=["aws"])


# ── Discovery endpoints ───────────────────────────────────────────────────────

@router.get("/ec2/asgs")
def list_asgs():
    return ec2_ctrl.list_asgs()

@router.get("/ecs/clusters")
def list_clusters():
    return ecs_ctrl.list_clusters()

@router.get("/ecs/{cluster}/services")
def list_services(cluster: str):
    return ecs_ctrl.list_services(cluster)

@router.get("/eks/clusters")
def list_eks_clusters():
    return eks_ctrl.list_clusters()

@router.get("/eks/{cluster}/nodegroups")
def list_nodegroups(cluster: str):
    return eks_ctrl.list_nodegroups(cluster)


# ── Cost endpoints ────────────────────────────────────────────────────────────

@router.get("/cost/current-month")
def current_month_cost():
    return cost_explorer.get_current_month_cost()

@router.get("/cost/daily")
def daily_cost(days: int = 7):
    return cost_explorer.get_daily_cost(days)

@router.get("/cost/forecast")
def cost_forecast(days_ahead: int = 30):
    return cost_explorer.get_cost_forecast(days_ahead)


# ── Manual scaling endpoints (for dashboard "Apply" buttons) ─────────────────

class ScalingAction(BaseModel):
    action: str          # "scale_up" | "scale_down" | "terminate_idle"
    resource_type: str   # "ec2" | "ecs" | "eks"
    target: dict
    params: dict = {}

@router.post("/scale")
def execute_scaling(body: ScalingAction):
    result = aws_executor.execute(body.dict())
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result