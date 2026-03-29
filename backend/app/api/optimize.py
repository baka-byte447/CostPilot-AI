from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.config.database import SessionLocal
from app.optimizer.safety_engine import get_slo_config

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/optimize/scale")
def optimize_cluster(db: Session = Depends(get_db)):
    from app.optimizer.scaling_decision import decide_scaling
    result = decide_scaling(db)
    return result


@router.get("/optimize/slo")
def get_slo():
    return get_slo_config()


@router.get("/optimize/safety/status")
def get_safety_status():
    from app.optimizer.safety_engine import SLO, _last_action_time
    import time
    seconds_since = time.time() - _last_action_time
    return {
        "cooldown_remaining": max(0, SLO.cooldown_seconds - int(seconds_since)),
        "cooldown_active": seconds_since < SLO.cooldown_seconds,
        "slo": get_slo_config()
    }