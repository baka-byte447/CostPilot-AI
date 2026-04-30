from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
import json
from datetime import datetime, timezone

from app.config.database import SessionLocal
from app.k8s.k8s_controller import scale_deployment
from app.optimizer.scaling_decision import decide_scaling
from app.optimizer.safety_engine import get_safety_status as safety_status
from app.optimizer.safety_engine import get_slo_config as slo_config
from app.optimizer.safety_engine import get_last_replicas
from app.optimizer.explainer import explain_decision
from app.api.dependencies import get_user_id

router = APIRouter(prefix="/optimize", tags=["optimize"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/scale", summary="Choose replica count via RL and apply to Kubernetes")
def optimize_cluster(db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    try:
        decision = decide_scaling(db)
        replicas = decision.get("replicas", 3) if isinstance(decision, dict) else decision
        if not isinstance(decision, dict):
            decision = {"action": "maintain", "replicas": replicas}
            
        current_replicas = get_last_replicas()
        result = scale_deployment(
            deployment_name="load-test-app",
            namespace="default",
            replicas=replicas,
        )
        if "replicas" not in result and "new_replicas" in result:
            result["replicas"] = result["new_replicas"]
        if "new_replicas" not in result and "replicas" in result:
            result["new_replicas"] = result["replicas"]
            
        explanation_data = explain_decision(decision)
        reason = explanation_data.get("explanation", "RL agent decision")
        
        db.execute(text(
            """
            INSERT INTO audit_log (timestamp, user_id, action, state_before, state_after, decision_rationale, status)
            VALUES (:ts, :uid, :act, :sb, :sa, :reason, :status)
            """
        ), {
            "ts": datetime.now(timezone.utc),
            "uid": user_id,
            "act": decision.get("action", "maintain"),
            "sb": json.dumps({"replicas": current_replicas}),
            "sa": json.dumps({"replicas": replicas}),
            "reason": reason,
            "status": "success"
        })
        db.commit()
            
        return result
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Scaling failed: {exc}")


@router.get("/preview", summary="Preview the recommended replica count without applying scaling")
def preview_scaling(db: Session = Depends(get_db)):
    try:
        decision = decide_scaling(db)
        replicas = decision.get("replicas", 3) if isinstance(decision, dict) else decision
    except Exception as exc:
        replicas = 3

    return {
        "deployment": "load-test-app",
        "recommended_replicas": replicas,
        "mode": "preview",
    }

@router.get("/slo")
def get_slo_config():
    return slo_config()

@router.get("/safety/status")
def get_safety_status():
    return safety_status()
