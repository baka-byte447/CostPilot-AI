from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.database import SessionLocal
from app.ml.forecasting_model import forecast_system_metrics

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db

    finally:
        db.close()

@router.get("/forecast/system")
def system_forecast(db: Session = Depends(get_db)):
    return forecast_system_metrics(db)