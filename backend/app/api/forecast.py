from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.database import SessionLocal
from app.ml.forecasting_model import forecast_system_metrics

router = APIRouter(prefix="/forecast", tags=["forecast"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/system", summary="Predict short-term CPU, memory, and request load")
def system_forecast(db: Session = Depends(get_db)):
    return forecast_system_metrics(db)