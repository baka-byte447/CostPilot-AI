from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.database import SessionLocal
from app.services.metrics_service import collect_and_store_metrics, get_all_metrics
from app.api.dependencies import get_user_id

router = APIRouter(prefix="/metrics", tags=["metrics"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/collect", summary="Collect and persist the latest metrics from Prometheus")
def collect_metrics(db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    return collect_and_store_metrics(db, user_id=user_id)


@router.get("", summary="Return all stored metrics ordered by recency")
def read_metrics(db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    data = get_all_metrics(db, user_id=user_id)
    return [
        {
            "id": item.id,
            "cpu_usage": item.cpu_usage,
            "memory_usage": item.memory_usage,
            "request_load": item.request_load,
            "timestamp": item.timestamp,
        }
        for item in data
    ]


