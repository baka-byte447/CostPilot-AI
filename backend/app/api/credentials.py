from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.core.deps import get_db, get_current_user
from app.core.security import encrypt_credentials, decrypt_credentials
from app.models.user_model import User, UserCredential

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
    return {"status": "ok", "provider": "azure", "subscription_id": body.subscription_id}


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
