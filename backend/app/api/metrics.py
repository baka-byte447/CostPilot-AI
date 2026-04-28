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
from app.models.cloud_status_model import CloudResourceStatus

@router.get("/metrics")
def read_metrics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    data = (
        db.query(Metrics)
        .filter_by(user_id=current_user.id)
        .order_by(Metrics.timestamp.asc())
        .all()
    )

    status_row = (
        db.query(CloudResourceStatus)
        .filter_by(user_id=current_user.id, provider="azure", resource_type="vmss")
        .first()
    )

    return {
        "meta": {
            "provider": "azure" if status_row else None,
            "data_source": status_row.data_source if status_row else None,
            "status": status_row.status if status_row else "not_configured",
            "vmss": (
                {
                    "subscription_id": status_row.subscription_id,
                    "resource_group": status_row.resource_group,
                    "name": status_row.resource_name,
                    "resource_id": status_row.resource_id,
                    "location": status_row.location,
                }
                if status_row
                else None
            ),
            "last_validated_at": status_row.last_validated_at.isoformat() if status_row and status_row.last_validated_at else None,
            "last_validation_error": status_row.last_validation_error if status_row else None,
            "last_metrics_at": status_row.last_metrics_at.isoformat() if status_row and status_row.last_metrics_at else None,
            "last_metrics_error": status_row.last_metrics_error if status_row else None,
        },
        "metrics": [
            {
                "id": item.id,
                "cpu_usage": item.cpu_usage,
                "memory_usage": item.memory_usage,
                "request_load": item.request_load,
                "is_simulated": bool(item.is_simulated),
                "timestamp": item.timestamp,
            }
            for item in data
        ],
    }


