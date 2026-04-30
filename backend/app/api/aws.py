from datetime import datetime
import secrets
import urllib.parse
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import get_aws_manager, get_db, get_user_id
from app.aws.iam_template import build_role_template
from app.config.settings import settings
from app.models.aws_connection import AwsConnection

router = APIRouter(prefix="/aws", tags=["aws"])


# ──────────────────────────── Schemas ────────────────────────────

class AwsSetupRequest(BaseModel):
    role_name: str = Field("CostPilotAccessRole", min_length=1, max_length=64)
    allow_write: bool = False


class AwsSetupResponse(BaseModel):
    external_id: str
    role_name: str
    control_account_id: str
    template_yaml: str
    cloudformation_url: str


class AwsConnectionInput(BaseModel):
    account_id: str = Field(..., min_length=8, max_length=32)
    role_arn: str = Field(..., min_length=20, max_length=256)
    external_id: str = Field(..., min_length=1, max_length=128)
    regions: List[str] = Field(default=["us-east-1"])
    label: Optional[str] = Field(None, max_length=128)


class AwsConnectionResponse(BaseModel):
    id: int
    account_id: str
    role_arn: str
    external_id_set: bool
    default_region: str
    regions: List[str]
    label: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AwsTemplateRequest(BaseModel):
    role_name: str = Field("CostPilotAccessRole", min_length=1, max_length=64)
    external_id: Optional[str] = Field(None, max_length=128)
    allow_write: bool = False


# ──────────────────────────── Helpers ────────────────────────────

def _serialize_connection(c: AwsConnection) -> dict:
    regions = [r.strip() for r in (c.regions or "us-east-1").split(",") if r.strip()]
    return {
        "id": c.id,
        "account_id": c.account_id,
        "role_arn": c.role_arn,
        "external_id_set": bool(c.external_id),
        "default_region": c.default_region,
        "regions": regions,
        "label": c.label,
        "is_active": c.is_active,
        "created_at": c.created_at,
        "updated_at": c.updated_at,
    }


def _build_cfn_quick_url(template_yaml: str, role_name: str) -> str:
    """Build an AWS CloudFormation quick-create stack URL.
    In production you'd host the template on S3; for now we encode it as a
    data-URI fallback and point the user at the console."""
    base = "https://console.aws.amazon.com/cloudformation/home#/stacks/quickcreate"
    params = urllib.parse.urlencode({
        "stackName": f"CostPilot-{role_name}",
        "param_RoleName": role_name,
    })
    return f"{base}?{params}"


# ──────── Step 1 — Generate External ID + CloudFormation ─────────

@router.post("/connection/setup", response_model=AwsSetupResponse)
def setup_connection(
    body: AwsSetupRequest,
    user_id: str = Depends(get_user_id),
):
    """Generate an External ID and a CloudFormation template for the user
    to deploy in their AWS account.  No credentials are collected here."""
    control_account_id = settings.aws_control_account_id or "000000000000"

    external_id = secrets.token_urlsafe(24)
    role_name = body.role_name.strip()

    template_yaml = build_role_template(
        control_account_id=control_account_id,
        external_id=external_id,
        role_name=role_name,
        allow_write=body.allow_write,
    )

    cfn_url = _build_cfn_quick_url(template_yaml, role_name)

    return {
        "external_id": external_id,
        "role_name": role_name,
        "control_account_id": control_account_id,
        "template_yaml": template_yaml,
        "cloudformation_url": cfn_url,
    }


# ──────── Step 2 — Save the connection (role ARN) ────────────────

@router.post("/connection", response_model=AwsConnectionResponse)
def upsert_connection(
    body: AwsConnectionInput,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    """Store the Role ARN + External ID that the user received from the
    CloudFormation deployment.  No access keys are ever stored."""
    regions_csv = ",".join([r.strip() for r in body.regions if r.strip()]) or "us-east-1"
    default_region = body.regions[0].strip() if body.regions else "us-east-1"

    connection = (
        db.query(AwsConnection)
        .filter(AwsConnection.user_id == user_id)
        .first()
    )

    if connection:
        connection.account_id = body.account_id.strip()
        connection.role_arn = body.role_arn.strip()
        connection.external_id = body.external_id.strip()
        connection.default_region = default_region
        connection.regions = regions_csv
        connection.label = body.label.strip() if body.label else None
        connection.is_active = True
    else:
        connection = AwsConnection(
            user_id=user_id,
            account_id=body.account_id.strip(),
            role_arn=body.role_arn.strip(),
            external_id=body.external_id.strip(),
            default_region=default_region,
            regions=regions_csv,
            label=body.label.strip() if body.label else None,
            is_active=True,
        )
        db.add(connection)

    db.commit()
    db.refresh(connection)
    return _serialize_connection(connection)


# ──────── Read / Delete / Verify ─────────────────────────────────

@router.get("/connection", response_model=AwsConnectionResponse)
def get_connection(
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    connection = (
        db.query(AwsConnection)
        .filter(AwsConnection.user_id == user_id, AwsConnection.is_active.is_(True))
        .first()
    )
    if not connection:
        raise HTTPException(status_code=404, detail="AWS connection not found")
    return _serialize_connection(connection)


@router.delete("/connection")
def delete_connection(
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    connection = (
        db.query(AwsConnection)
        .filter(AwsConnection.user_id == user_id, AwsConnection.is_active.is_(True))
        .first()
    )
    if not connection:
        raise HTTPException(status_code=404, detail="AWS connection not found")
    connection.is_active = False
    db.commit()
    return {"success": True}


@router.get("/connection/verify")
def verify_connection(aws_manager=Depends(get_aws_manager)):
    try:
        ident = aws_manager.sts().get_caller_identity()
        return {"verified": True, "account_id": ident.get("Account"), "arn": ident.get("Arn")}
    except Exception as e:
        return {"verified": False, "error": str(e)}


# ──────── Legacy template endpoint (kept for backwards compat) ───

@router.post("/connection/template")
def get_connection_template(
    body: AwsTemplateRequest,
    user_id: str = Depends(get_user_id),
):
    if not settings.aws_control_account_id:
        raise HTTPException(
            status_code=400,
            detail="AWS_CONTROL_ACCOUNT_ID is not configured",
        )
    external_id = (body.external_id or "").strip() or secrets.token_urlsafe(16)
    template = build_role_template(
        control_account_id=settings.aws_control_account_id,
        external_id=external_id,
        role_name=body.role_name.strip(),
        allow_write=body.allow_write,
    )
    return {
        "external_id": external_id,
        "role_name": body.role_name.strip(),
        "control_account_id": settings.aws_control_account_id,
        "template": template,
    }


# ──────── AWS Resource Endpoints (unchanged) ─────────────────────

@router.get("/ec2/asgs")
def list_asgs(aws_manager=Depends(get_aws_manager)):
    try:
        from app.aws import get_ec2_ctrl
        return get_ec2_ctrl(aws_manager).list_asgs()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AWS unavailable: {str(e)}")


@router.get("/ecs/clusters")
def list_clusters(aws_manager=Depends(get_aws_manager)):
    try:
        from app.aws import get_ecs_ctrl
        return get_ecs_ctrl(aws_manager).list_clusters()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AWS unavailable: {str(e)}")


@router.get("/ecs/{cluster}/services")
def list_services(cluster: str, aws_manager=Depends(get_aws_manager)):
    try:
        from app.aws import get_ecs_ctrl
        return get_ecs_ctrl(aws_manager).list_services(cluster)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AWS unavailable: {str(e)}")


@router.get("/eks/clusters")
def list_eks_clusters(aws_manager=Depends(get_aws_manager)):
    try:
        from app.aws import get_eks_ctrl
        return get_eks_ctrl(aws_manager).list_clusters()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AWS unavailable: {str(e)}")


@router.get("/eks/{cluster}/nodegroups")
def list_nodegroups(cluster: str, aws_manager=Depends(get_aws_manager)):
    try:
        from app.aws import get_eks_ctrl
        return get_eks_ctrl(aws_manager).list_nodegroups(cluster)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AWS unavailable: {str(e)}")


@router.get("/cost/current-month")
def current_month_cost(aws_manager=Depends(get_aws_manager)):
    try:
        from app.aws import get_cost_explorer
        return get_cost_explorer(aws_manager).get_current_month_cost()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AWS unavailable: {str(e)}")


@router.get("/cost/daily")
def daily_cost(days: int = 7, aws_manager=Depends(get_aws_manager)):
    try:
        from app.aws import get_cost_explorer
        return get_cost_explorer(aws_manager).get_daily_cost(days)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AWS unavailable: {str(e)}")


@router.get("/cost/forecast")
def cost_forecast(days_ahead: int = 30, aws_manager=Depends(get_aws_manager)):
    try:
        from app.aws import get_cost_explorer
        return get_cost_explorer(aws_manager).get_cost_forecast(days_ahead)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AWS unavailable: {str(e)}")


class ScalingAction(BaseModel):
    action: str
    resource_type: str
    target: dict
    params: dict = {}


@router.post("/scale")
def execute_scaling(body: ScalingAction, aws_manager=Depends(get_aws_manager)):
    try:
        from app.optimizer.aws_scaling_executor import aws_executor
        result = aws_executor.execute(body.dict(), aws_manager=aws_manager)
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