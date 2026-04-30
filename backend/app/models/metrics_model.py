from sqlalchemy import Column, Integer, Float, DateTime, String
from datetime import datetime, timezone
from app.config.database import Base

class Metrics(Base):
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=True)
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    request_load = Column(Float)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))