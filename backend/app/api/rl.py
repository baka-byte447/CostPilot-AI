import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.config.database import SessionLocal

router = APIRouter(prefix="/rl", tags=["rl"])
logger = logging.getLogger(__name__)

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
        from app.workers.metrics_collector import set_last_explanation

        cpu    = fetch_prometheus_data(CPU_QUERY)
        memory = fetch_prometheus_data(MEMORY_QUERY)
        req    = fetch_prometheus_data(REQUEST_QUERY)

        decision = decide_scaling_with_rl(cpu, memory, req)
        explanation = explain_decision(decision)
        try:
            set_last_explanation(explanation)
        except Exception:
            pass

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
        from app.aws import get_ec2_ctrl, get_ecs_ctrl, get_eks_ctrl

        ec2_ctrl = get_ec2_ctrl()
        ecs_ctrl = get_ecs_ctrl()
        eks_ctrl = get_eks_ctrl()

        asgs = ec2_ctrl.list_asgs()

        ecs = {}
        for cluster in ecs_ctrl.list_clusters():
            ecs[cluster] = ecs_ctrl.list_services(cluster)

        eks = {}
        for cluster in eks_ctrl.list_clusters():
            eks[cluster] = eks_ctrl.list_nodegroups(cluster)

        return {
            "source": "real",
            "asgs": asgs,
            "ecs": ecs,
            "eks": eks,
            "recent_actions": []
        }
    except Exception as e:
        logger.warning("Falling back to mock AWS state: %s", e)
        try:
            from app.aws.mock_aws import _state, get_actions_log
            return {
                "source": "mock",
                "asgs": list(_state["asgs"].values()),
                "ecs": {
                    cluster: list(data["services"].values())
                    for cluster, data in _state["ecs_clusters"].items()
                },
                "eks": {
                    cluster: list(data["nodegroups"].values())
                    for cluster, data in _state["eks_clusters"].items()
                },
                "recent_actions": get_actions_log()[:10],
                "error": str(e)
            }
        except Exception as inner:
            return {"source": "mock", "error": str(inner)}