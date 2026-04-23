import schedule
import time
import logging
import os
from sqlalchemy.orm import Session
from app.config.database import SessionLocal
from app.services.metrics_service import collect_and_store_metrics

logger    = logging.getLogger(__name__)
AZURE_MODE = os.getenv("AZURE_MODE", "false").lower() == "true"

_last_explanation = None


def get_last_explanation() -> dict:
    return _last_explanation


def _get_forecast(db: Session) -> dict:
    try:
        from app.cost.cost_forecast import forecast_cost
        return forecast_cost(db)
    except Exception as e:
        logger.warning(f"Forecast unavailable: {e}")
        return {"forecast_available": False}


def run_rl_decision(metrics: dict, forecast: dict = None, creds: dict = None):
    global _last_explanation
    try:
        from app.rl.trainer import decide_scaling_with_rl
        from app.optimizer.explainer import explain_decision

        decision = decide_scaling_with_rl(
            cpu=metrics["cpu_usage"],
            memory=metrics["memory_usage"],
            request_load=metrics["request_load"],
            forecast=forecast,
            creds=creds
        )

        forecast_info = ""
        if forecast and forecast.get("forecast_available"):
            forecast_info = (
                f"| forecast_cpu={forecast.get('worst_case_cpu')} "
                f"forecast_mem={forecast.get('worst_case_memory')}"
            )

        logger.info(
            f"RL Decision: {decision['action']} | "
            f"CPU={decision['cpu']}% | "
            f"reward={decision['reward']} | "
            f"ε={decision['epsilon']} {forecast_info}"
        )

        explanation = explain_decision(decision)
        _last_explanation = explanation
        logger.info(f"Explanation [{explanation['source']}]: {explanation['explanation'][:80]}...")

        if AZURE_MODE:
            _dispatch_azure(decision, creds)

        return decision

    except Exception as e:
        logger.error(f"RL decision failed: {e}", exc_info=True)
        return None


def _dispatch_azure(decision: dict, creds: dict = None):
    try:
        from app.optimizer.azure_scaling_executor import azure_executor
        result = azure_executor.execute({
            "action":        decision["action"],
            "resource_type": "aci",
            "target":        {},
            "params":        {"increment": 1, "decrement": 1}
        }, creds)
        if result.get("success"):
            logger.info(f"Azure action applied: {result.get('action')} on ACI")
        else:
            logger.warning(f"Azure action failed: {result.get('error')}")
    except Exception as e:
        logger.error(f"Azure dispatch failed: {e}")


def job():
    db: Session = SessionLocal()
    try:
        metrics  = collect_and_store_metrics(db)
        logger.info(
            f"Metrics collected: CPU={metrics['cpu_usage']:.1f}% "
            f"MEM={metrics['memory_usage']:.1f}% "
            f"REQ={metrics['request_load']:.4f}"
        )
        forecast = _get_forecast(db)

        # Single-tenant approach: grab the first user's credentials
        from app.models.user_model import User
        from app.api.credentials import load_user_credentials
        
        user = db.query(User).first()
        creds = None
        if user:
            provider = "azure" if AZURE_MODE else "aws"
            creds = load_user_credentials(user.id, provider, db)
            if creds:
                logger.info(f"Loaded {provider} credentials for user {user.email}")
            else:
                logger.warning(f"User {user.email} has no {provider} credentials. Falling back to .env.")
        else:
            logger.warning("No users registered. Falling back to .env credentials.")

        run_rl_decision(metrics, forecast, creds)
    except Exception as e:
        logger.error(f"Collector job failed: {e}", exc_info=True)
    finally:
        db.close()


def start_scheduler():
    logger.info("Starting metrics collector + RL agent loop (10s interval)")
    schedule.every(10).seconds.do(job)
    while True:
        schedule.run_pending()
        time.sleep(1)

        