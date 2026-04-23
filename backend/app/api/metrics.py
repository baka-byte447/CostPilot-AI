from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.config.database import SessionLocal
from app.services.metrics_service import collect_and_store_metrics, get_all_metrics

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/collect")
def collect_metrics(db:Session = Depends(get_db)):
    return collect_and_store_metrics(db)

from app.core.deps import get_current_user
from app.models.user_model import User
from app.models.metrics_model import Metrics

@router.get("/metrics")
def read_metrics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    data = db.query(Metrics).filter_by(user_id=current_user.id).order_by(Metrics.timestamp.asc()).all()
    if not data:
        # Fallback to demo metrics (user_id=None) if empty
        data = db.query(Metrics).filter_by(user_id=None).order_by(Metrics.timestamp.asc()).all()
        
    return [{"id": item.id,
             "cpu_usage": item.cpu_usage,
             "memory_usage": item.memory_usage,
             "request_load": item.request_load,
             "is_simulated": bool(item.is_simulated),
             "timestamp": item.timestamp}
            for item in data]


