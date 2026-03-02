from sqlalchemy import Column, Integer, Float, DateTime
from datetime import datetime
from app.config.database import Base

class Metrics(Base):
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)