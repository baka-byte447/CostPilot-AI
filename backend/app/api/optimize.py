from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.config.database import SessionLocal
from app.k8s.k8s_controller import scale_deployment
from app.optimizer.scaling_decision import decide_scaling

router = APIRouter(prefix="/optimize", tags=["optimize"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/scale", summary="Choose replica count via RL and apply to Kubernetes")
def optimize_cluster(db: Session = Depends(get_db)):
    try:
        replicas = decide_scaling(db)
        result = scale_deployment(
            deployment_name="load-test-app",
            namespace="default",
            replicas=replicas,
        )
        return result
    except Exception as exc:
        # Fallback if Kubernetes isn't available
        return {"status": "scaled_mock", "replicas": 3, "namespace": "default", "message": str(exc)}


@router.get("/preview", summary="Preview the recommended replica count without applying scaling")
def preview_scaling(db: Session = Depends(get_db)):
    try:
        replicas = decide_scaling(db)
    except Exception as exc:
        replicas = 3

    return {
        "deployment": "load-test-app",
        "recommended_replicas": replicas,
        "mode": "preview",
    }

@router.get("/slo")
def get_slo_config():
    """Mock SLO endpoint."""
    return {
        "target_response_time_ms": 200,
        "error_budget_percent": 1,
        "max_pod_utilization": 80,
    }

@router.get("/safety/status")
def get_safety_status():
    """Mock safety status endpoint."""
    return {
        "cooldown_active": False,
        "cooldown_remaining": 0,
        "last_action_time": datetime.utcnow().isoformat(),
        "circuit_breaker": "CLOSED",
    }
