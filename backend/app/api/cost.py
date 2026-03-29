from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.config.database import SessionLocal
from app.cost.cost_forecast import forecast_cost

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/forecast/cost")
def cost_prediction(db: Session = Depends(get_db)):
    return forecast_cost(db)