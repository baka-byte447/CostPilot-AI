from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/aws", tags=["aws"])


@router.get("/ec2/asgs")
def list_asgs():
    try:
        from app.aws import get_ec2_ctrl
        return get_ec2_ctrl().list_asgs()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AWS unavailable: {str(e)}")


@router.get("/ecs/clusters")
def list_clusters():
    try:
        from app.aws import get_ecs_ctrl
        return get_ecs_ctrl().list_clusters()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AWS unavailable: {str(e)}")


@router.get("/ecs/{cluster}/services")
def list_services(cluster: str):
    try:
        from app.aws import get_ecs_ctrl
        return get_ecs_ctrl().list_services(cluster)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AWS unavailable: {str(e)}")


@router.get("/eks/clusters")
def list_eks_clusters():
    try:
        from app.aws import get_eks_ctrl
        return get_eks_ctrl().list_clusters()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AWS unavailable: {str(e)}")


@router.get("/eks/{cluster}/nodegroups")
def list_nodegroups(cluster: str):
    try:
        from app.aws import get_eks_ctrl
        return get_eks_ctrl().list_nodegroups(cluster)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AWS unavailable: {str(e)}")


@router.get("/cost/current-month")
def current_month_cost():
    try:
        from app.aws import get_cost_explorer
        return get_cost_explorer().get_current_month_cost()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AWS unavailable: {str(e)}")


@router.get("/cost/daily")
def daily_cost(days: int = 7):
    try:
        from app.aws import get_cost_explorer
        return get_cost_explorer().get_daily_cost(days)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AWS unavailable: {str(e)}")


@router.get("/cost/forecast")
def cost_forecast(days_ahead: int = 30):
    try:
        from app.aws import get_cost_explorer
        return get_cost_explorer().get_cost_forecast(days_ahead)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AWS unavailable: {str(e)}")


class ScalingAction(BaseModel):
    action: str
    resource_type: str
    target: dict
    params: dict = {}


@router.post("/scale")
def execute_scaling(body: ScalingAction):
    try:
        from app.optimizer.aws_scaling_executor import aws_executor
        result = aws_executor.execute(body.dict())
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AWS unavailable: {str(e)}")


@router.get("/actions/log")
def get_actions_log():
    from app.aws.mock_aws import get_actions_log
    return get_actions_log()

@router.get("/state")
def get_full_state():
    from app.aws.mock_aws import _state
    return {
        "asgs": list(_state["asgs"].values()),
        "ecs_clusters": {
            cluster: {
                "services": list(data["services"].values())
            }
            for cluster, data in _state["ecs_clusters"].items()
        },
        "eks_clusters": {
            cluster: {
                "nodegroups": list(data["nodegroups"].values())
            }
            for cluster, data in _state["eks_clusters"].items()
        }
    }