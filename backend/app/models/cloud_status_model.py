from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.config.database import Base


class CloudResourceStatus(Base):
    __tablename__ = "cloud_resource_status"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)

    provider = Column(String, nullable=False)  # e.g. "azure"
    resource_type = Column(String, nullable=False)  # e.g. "vmss"

    subscription_id = Column(String, nullable=True)
    resource_group = Column(String, nullable=True)
    resource_name = Column(String, nullable=True)  # vmss name
    resource_id = Column(Text, nullable=True)  # Azure resourceId when known
    location = Column(String, nullable=True)

    status = Column(String, nullable=False, default="not_configured")  # ok|degraded|error|not_configured
    data_source = Column(String, nullable=True)  # e.g. "azure_monitor"

    last_validated_at = Column(DateTime, nullable=True)
    last_validation_error = Column(Text, nullable=True)

    last_metrics_at = Column(DateTime, nullable=True)
    last_metrics_error = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

