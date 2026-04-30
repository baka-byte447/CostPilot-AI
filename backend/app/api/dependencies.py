from typing import Generator, Optional

from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app.aws.aws_client import AWSClientManager, get_default_aws_manager
from app.config.database import SessionLocal
from app.config.settings import settings
from app.models.aws_connection import AwsConnection


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


security = HTTPBearer(auto_error=False)

def decode_access_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

def get_user_id(creds: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> str:
    if creds:
        return decode_access_token(creds.credentials)
    
    if not settings.auth_required:
        return "default"
        
    raise HTTPException(status_code=401, detail="Not authenticated")


def get_aws_manager(
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> AWSClientManager:
    connection = (
        db.query(AwsConnection)
        .filter(AwsConnection.user_id == user_id, AwsConnection.is_active.is_(True))
        .first()
    )
    if not connection:
        if settings.aws_require_connection:
            raise HTTPException(status_code=404, detail="AWS connection not found for user")
        return get_default_aws_manager()

    external_id = connection.external_id.strip() if connection.external_id else None
    region = connection.default_region or settings.aws_default_region
    return AWSClientManager.from_assumed_role(
        role_arn=connection.role_arn,
        external_id=external_id,
        region=region,
        duration_seconds=settings.aws_assume_role_duration_seconds,
    )
