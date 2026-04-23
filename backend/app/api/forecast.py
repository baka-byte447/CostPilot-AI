from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.config.database import SessionLocal

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


from app.core.deps import get_current_user
from app.models.user_model import User

@router.get("/forecast/system")
def system_forecast(
    db: Session = Depends(get_db),
    model: str = Query("auto", description="Forecasting model: auto | lstm | prophet"),
    retrain: bool = Query(False, description="Force LSTM retrain from scratch"),
    current_user: User = Depends(get_current_user)
):
    from app.ml.forecasting_model import forecast_system_metrics
    return forecast_system_metrics(db, user_id=current_user.id, model=model, retrain=retrain)


@router.get("/forecast/cost")
def cost_forecast(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.cost.cost_forecast import forecast_cost
    return forecast_cost(db, user_id=current_user.id)


@router.get("/forecast/rl-aware")
def rl_aware_forecast(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.cost.cost_forecast import forecast_cost
    from app.rl.trainer import decide_scaling_with_rl
    from app.services.metrics_service import fetch_prometheus_data
    from app.services.metrics_service import CPU_QUERY, MEMORY_QUERY, REQUEST_QUERY

    forecast = forecast_cost(db, user_id=current_user.id)
    cpu      = fetch_prometheus_data(CPU_QUERY)
    memory   = fetch_prometheus_data(MEMORY_QUERY)
    req      = fetch_prometheus_data(REQUEST_QUERY)

    from app.api.credentials import load_user_credentials
    import os
    AZURE_MODE = os.getenv("AZURE_MODE", "false").lower() == "true"
    
    provider = "azure" if AZURE_MODE else "aws"
    creds = load_user_credentials(current_user.id, provider, db)

    decision = decide_scaling_with_rl(current_user.id, cpu, memory, req, forecast=forecast, creds=creds)

    return {
        "forecast":            forecast,
        "decision":            decision,
        "forecast_influenced": decision.get("forecast") is not None
    }


@router.post("/forecast/lstm/retrain")
def retrain_lstm(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.ml.forecasting_model import forecast_system_metrics
    return forecast_system_metrics(db, user_id=current_user.id, model="lstm", retrain=True)


@router.get("/forecast/db/cleanup")
def run_db_cleanup():
    from app.utils.cleanup_db import cleanup_negative_metrics
    return cleanup_negative_metrics()
