from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.database import SessionLocal
from app.ml.forecasting_model import train_cpu_forecast_model

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db

    finally:
        db.close()

@router.get("/forecast/cpu")
def cpu_forecast(db: Session = Depends(get_db)):
    return train_cpu_forecast_model(db)