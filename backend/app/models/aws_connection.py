from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app.config.database import Base


class AwsConnection(Base):
    __tablename__ = "aws_connections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(128), index=True, nullable=False)
    account_id = Column(String(32), nullable=False)
    role_arn = Column(String(256), nullable=False)
    external_id = Column(String(128), nullable=False)
    default_region = Column(String(32), nullable=False, default="us-east-1")
    regions = Column(String(512), nullable=False, default="us-east-1")
    label = Column(String(128), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
