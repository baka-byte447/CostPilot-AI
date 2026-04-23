from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.config.database import SessionLocal

router = APIRouter(prefix="/rl", tags=["rl"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
@router.get("/stats")
def get_rl_stats():
    try:
        from app.rl.trainer import get_agent_stats
        return get_agent_stats()
    except Exception as e:
        return {"error": str(e)}


from app.core.deps import get_current_user
from app.models.user_model import User

@router.get("/decision/latest")
def get_latest_decision(current_user: User = Depends(get_current_user)):
    try:
        from app.services.metrics_service import fetch_prometheus_data
        from app.services.metrics_service import CPU_QUERY, MEMORY_QUERY, REQUEST_QUERY
        from app.rl.trainer import decide_scaling_with_rl
        from app.optimizer.explainer import explain_decision

        cpu    = fetch_prometheus_data(CPU_QUERY)
        memory = fetch_prometheus_data(MEMORY_QUERY)
        req    = fetch_prometheus_data(REQUEST_QUERY)

        db = next(get_db())
        from app.api.credentials import load_user_credentials
        import os
        AZURE_MODE = os.getenv("AZURE_MODE", "false").lower() == "true"
        provider = "azure" if AZURE_MODE else "aws"
        creds = load_user_credentials(current_user.id, provider, db)

        decision = decide_scaling_with_rl(current_user.id, cpu, memory, req, forecast=None, creds=creds)
        explanation = explain_decision(decision)

        return {"status": "ok", "decision": decision, "explanation": explanation}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.get("/explanation/latest")
def get_latest_explanation(current_user: User = Depends(get_current_user)):
    try:
        from app.workers.user_metrics_collector import get_last_explanation
        explanation = get_last_explanation(current_user.id)
        if not explanation:
            return {"status": "no_explanation_yet"}
        return {"status": "ok", "explanation": explanation}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.get("/aws/state")
def get_aws_state():
    try:
        from app.aws.mock_aws import _state, get_actions_log
        return {
            "asgs": list(_state["asgs"].values()),
            "ecs": {
                cluster: list(data["services"].values())
                for cluster, data in _state["ecs_clusters"].items()
            },
            "eks": {
                cluster: list(data["nodegroups"].values())
                for cluster, data in _state["eks_clusters"].items()
            },
            "recent_actions": get_actions_log()[:10]
        }
    except Exception as e:
        return {"error": str(e)}