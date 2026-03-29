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


@router.get("/decision/latest")
def get_latest_decision():
    try:
        from app.services.metrics_service import fetch_prometheus_data
        from app.services.metrics_service import CPU_QUERY, MEMORY_QUERY, REQUEST_QUERY
        from app.rl.trainer import decide_scaling_with_rl
        from app.optimizer.explainer import explain_decision

        cpu    = fetch_prometheus_data(CPU_QUERY)
        memory = fetch_prometheus_data(MEMORY_QUERY)
        req    = fetch_prometheus_data(REQUEST_QUERY)

        decision = decide_scaling_with_rl(cpu, memory, req)
        explanation = explain_decision(decision)

        return {"status": "ok", "decision": decision, "explanation": explanation}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.get("/explanation/latest")
def get_latest_explanation():
    try:
        from app.workers.metrics_collector import get_last_explanation
        explanation = get_last_explanation()
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