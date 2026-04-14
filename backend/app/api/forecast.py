from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.config.database import SessionLocal

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/forecast/system")
def system_forecast(db: Session = Depends(get_db)):
    from app.ml.forecasting_model import forecast_system_metrics
    return forecast_system_metrics(db)


@router.get("/forecast/cost")
def cost_forecast(db: Session = Depends(get_db)):
    from app.cost.cost_forecast import forecast_cost
    return forecast_cost(db)


@router.get("/forecast/rl-aware")
def rl_aware_forecast(db: Session = Depends(get_db)):
    from app.cost.cost_forecast import forecast_cost
    from app.rl.trainer import decide_scaling_with_rl
    from app.services.metrics_service import fetch_prometheus_data
    from app.services.metrics_service import CPU_QUERY, MEMORY_QUERY, REQUEST_QUERY

    forecast = forecast_cost(db)
    cpu      = fetch_prometheus_data(CPU_QUERY)
    memory   = fetch_prometheus_data(MEMORY_QUERY)
    req      = fetch_prometheus_data(REQUEST_QUERY)

    decision = decide_scaling_with_rl(cpu, memory, req, forecast=forecast)

    return {
        "forecast":  forecast,
        "decision":  decision,
        "forecast_influenced": decision.get("forecast") is not None
    }


