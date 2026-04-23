from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from datetime import datetime
from app.config.database import Base

class Metrics(Base):
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=True)
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    request_load = Column(Float)
    is_simulated = Column(Integer, default=0) # 0 for false, 1 for true
    timestamp = Column(DateTime, default=datetime.utcnow)