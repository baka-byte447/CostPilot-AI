from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.core.deps import get_db, get_current_user
from app.core.security import encrypt_credentials, decrypt_credentials
from app.models.user_model import User, UserCredential
from app.models.cloud_status_model import CloudResourceStatus

router = APIRouter(prefix="/credentials", tags=["credentials"])

ALLOWED_PROVIDERS = {"aws", "azure"}


class AWSCredentials(BaseModel):
    access_key_id: str
    secret_access_key: str
    region: str = "us-east-1"
    endpoint_url: Optional[str] = None


class AzureCredentials(BaseModel):
    client_id: str
    client_secret: str
    tenant_id: str
    subscription_id: str
    resource_group: str = "costpilot-rg"
    location: str = "eastus"
    vmss_name: str


def _upsert_credential(db: Session, user_id: int, provider: str, data: dict) -> UserCredential:
    row = db.query(UserCredential).filter_by(user_id=user_id, provider=provider).first()
    encrypted = encrypt_credentials(data)
    if row:
        row.encrypted_credentials = encrypted
    else:
        row = UserCredential(user_id=user_id, provider=provider, encrypted_credentials=encrypted)
        db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _upsert_azure_vmss_status(db: Session, user_id: int, body: AzureCredentials) -> CloudResourceStatus:
    row = (
        db.query(CloudResourceStatus)
        .filter_by(user_id=user_id, provider="azure", resource_type="vmss")
        .first()
    )
    if not row:
        row = CloudResourceStatus(user_id=user_id, provider="azure", resource_type="vmss")
        db.add(row)

    row.subscription_id = body.subscription_id
    row.resource_group = body.resource_group
    row.resource_name = body.vmss_name
    row.location = body.location
    row.data_source = "azure_monitor"
    if row.status == "not_configured":
        row.status = "degraded"
    db.commit()
    db.refresh(row)
    return row


@router.post("/aws", status_code=status.HTTP_200_OK)
def save_aws_credentials(
    body: AWSCredentials,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _upsert_credential(db, current_user.id, "aws", body.model_dump())
    return {"status": "ok", "provider": "aws", "region": body.region}


@router.post("/azure", status_code=status.HTTP_200_OK)
def save_azure_credentials(
    body: AzureCredentials,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _upsert_credential(db, current_user.id, "azure", body.model_dump())
    status_row = _upsert_azure_vmss_status(db, current_user.id, body)
    return {
        "status": "ok",
        "provider": "azure",
        "subscription_id": body.subscription_id,
        "vmss": {
            "resource_group": status_row.resource_group,
            "name": status_row.resource_name,
            "location": status_row.location,
        },
        "next": {"validate_url": "/credentials/azure/validate"},
    }


@router.post("/azure/validate", status_code=status.HTTP_200_OK)
def validate_azure_vmss_access(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Validates that the saved Azure Service Principal can read VMSS metadata and Azure Monitor metrics.
    This is required to ensure the dashboard shows real service data (not simulated).
    """
    creds = load_user_credentials(current_user.id, "azure", db)
    if not creds:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No Azure credentials found for this user")

    status_row = (
        db.query(CloudResourceStatus)
        .filter_by(user_id=current_user.id, provider="azure", resource_type="vmss")
        .first()
    )
    if not status_row or not status_row.resource_group or not status_row.resource_name or not status_row.subscription_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Azure VMSS is not configured. Save Azure credentials with vmss_name first.",
        )

    from datetime import datetime, timedelta, timezone
    from azure.core.exceptions import HttpResponseError, ResourceNotFoundError
    from azure.identity import ClientSecretCredential
    from azure.mgmt.compute import ComputeManagementClient
    from azure.mgmt.monitor import MonitorManagementClient

    credential = ClientSecretCredential(
        tenant_id=creds.get("tenant_id", ""),
        client_id=creds.get("client_id", ""),
        client_secret=creds.get("client_secret", ""),
    )
    subscription_id = status_row.subscription_id
    resource_group = status_row.resource_group
    vmss_name = status_row.resource_name

    try:
        compute = ComputeManagementClient(credential, subscription_id)
        monitor = MonitorManagementClient(credential, subscription_id)

        vmss = compute.virtual_machine_scale_sets.get(resource_group, vmss_name)
        status_row.resource_id = vmss.id

        # NOTE: Azure Monitor expects ISO8601; avoid "+00:00" in query params because "+" can be decoded as space.
        now = datetime.now(timezone.utc)
        start = now - timedelta(minutes=10)
        timespan = f"{start.strftime('%Y-%m-%dT%H:%M:%SZ')}/{now.strftime('%Y-%m-%dT%H:%M:%SZ')}"

        metrics_data = monitor.metrics.list(
            resource_uri=vmss.id,
            timespan=timespan,
            interval="PT1M",
            metricnames="Percentage CPU,Network In,Network Out",
            aggregation="Average,Total",
        )

        available = [m.name.value for m in (metrics_data.value or [])]
        status_row.status = "ok"
        status_row.last_validated_at = datetime.utcnow()
        status_row.last_validation_error = None
        db.commit()

        return {
            "status": "ok",
            "provider": "azure",
            "resource_type": "vmss",
            "vmss": {
                "subscription_id": subscription_id,
                "resource_group": resource_group,
                "name": vmss_name,
                "resource_id": vmss.id,
                "location": getattr(vmss, "location", None),
            },
            "data_source": "azure_monitor",
            "metrics_checked": available,
            "rbac_required": [
                {"role": "Reader", "scope_hint": f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}"},
                {"role": "Monitoring Reader", "scope_hint": f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}"},
            ],
        }
    except ResourceNotFoundError:
        status_row.status = "error"
        status_row.last_validated_at = datetime.utcnow()
        status_row.last_validation_error = f"VMSS not found: {resource_group}/{vmss_name}"
        db.commit()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=status_row.last_validation_error)
    except HttpResponseError as e:
        code = getattr(e, "status_code", None) or 503
        msg = str(e)
        status_row.status = "error" if code in (401, 403) else "degraded"
        status_row.last_validated_at = datetime.utcnow()
        status_row.last_validation_error = msg
        db.commit()

        if code in (401, 403):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": "Azure authorization failed while validating VMSS metrics access.",
                    "azure_error": msg,
                    "rbac_required": [
                        {"role": "Reader", "scope": f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}"},
                        {"role": "Monitoring Reader", "scope": f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}"},
                    ],
                    "next_steps": [
                        "Assign the roles above to the Service Principal (client_id) at the resource group or VMSS scope.",
                        "Wait a minute for permissions to propagate, then click Retry validation.",
                    ],
                },
            )
        raise HTTPException(status_code=503, detail=msg)
    except Exception as e:
        status_row.status = "degraded"
        status_row.last_validated_at = datetime.utcnow()
        status_row.last_validation_error = str(e)
        db.commit()
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/azure/status")
def get_azure_vmss_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = (
        db.query(CloudResourceStatus)
        .filter_by(user_id=current_user.id, provider="azure", resource_type="vmss")
        .first()
    )
    if not row:
        return {"status": "not_configured"}
    return {
        "status": row.status,
        "provider": row.provider,
        "resource_type": row.resource_type,
        "data_source": row.data_source,
        "vmss": {
            "subscription_id": row.subscription_id,
            "resource_group": row.resource_group,
            "name": row.resource_name,
            "resource_id": row.resource_id,
            "location": row.location,
        },
        "last_validated_at": row.last_validated_at.isoformat() if row.last_validated_at else None,
        "last_validation_error": row.last_validation_error,
        "last_metrics_at": row.last_metrics_at.isoformat() if row.last_metrics_at else None,
        "last_metrics_error": row.last_metrics_error,
    }


@router.get("")
def list_credentials(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.query(UserCredential).filter_by(user_id=current_user.id).all()
    result = []
    for row in rows:
        try:
            data = decrypt_credentials(row.encrypted_credentials)
            safe = {"provider": row.provider, "connected": True, "created_at": row.created_at.isoformat()}
            if row.provider == "aws":
                safe["region"] = data.get("region")
                safe["access_key_id_hint"] = data.get("access_key_id", "")[:4] + "****"
            elif row.provider == "azure":
                safe["subscription_id"] = data.get("subscription_id")
                safe["client_id_hint"] = data.get("client_id", "")[:8] + "****"
            result.append(safe)
        except Exception:
            result.append({"provider": row.provider, "connected": False, "error": "decryption_failed"})
    return {"credentials": result}


@router.delete("/{provider}", status_code=status.HTTP_200_OK)
def delete_credentials(
    provider: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if provider not in ALLOWED_PROVIDERS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown provider: {provider}")
    row = db.query(UserCredential).filter_by(user_id=current_user.id, provider=provider).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No {provider} credentials found")
    db.delete(row)
    db.commit()
    return {"status": "deleted", "provider": provider}


def load_user_credentials(user_id: int, provider: str, db: Session) -> Optional[dict]:
    row = db.query(UserCredential).filter_by(user_id=user_id, provider=provider).first()
    if not row:
        return None
    return decrypt_credentials(row.encrypted_credentials)
