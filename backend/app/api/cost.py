from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.database import SessionLocal
from app.cost.cost_forecast import forecast_cost

router = APIRouter(prefix="/cost", tags=["cost"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/forecast", summary="Estimate required instances and hourly cost")
def cost_prediction(db: Session = Depends(get_db)):
    return forecast_cost(db)