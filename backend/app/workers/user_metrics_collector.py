import schedule
import time
import logging
import random
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.config.database import SessionLocal
from app.models.user_model import User
from app.models.metrics_model import Metrics
from app.api.credentials import load_user_credentials
from app.services.metrics_service import fetch_prometheus_data, CPU_QUERY, MEMORY_QUERY, REQUEST_QUERY, _clamp

logger = logging.getLogger(__name__)

_last_explanation_dict = {}

def get_last_explanation(user_id: int) -> dict:
    return _last_explanation_dict.get(user_id)

def _get_forecast(db: Session, user_id: int) -> dict:
    try:
        from app.cost.cost_forecast import forecast_cost
        return forecast_cost(db, user_id)
    except Exception as e:
        logger.warning(f"Forecast unavailable for user {user_id}: {e}")
        return {"forecast_available": False}

def run_rl_decision(user_id: int, metrics: dict, forecast: dict = None, creds: dict = None, provider: str = None):
    global _last_explanation_dict
    try:
        from app.rl.trainer import decide_scaling_with_rl
        from app.optimizer.explainer import explain_decision

        decision = decide_scaling_with_rl(
            user_id=user_id,
            cpu=metrics["cpu_usage"],
            memory=metrics["memory_usage"],
            request_load=metrics["request_load"],
            forecast=forecast,
            creds=creds
        )

        explanation = explain_decision(decision)
        _last_explanation_dict[user_id] = explanation

        if provider == "azure":
            _dispatch_azure(decision, creds)

        return decision

    except Exception as e:
        logger.error(f"RL decision failed for user {user_id}: {e}", exc_info=True)
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

def pull_aws_metrics(creds: dict):
    import boto3
    try:
        cloudwatch = boto3.client(
            'cloudwatch',
            aws_access_key_id=creds.get('access_key_id'),
            aws_secret_access_key=creds.get('secret_access_key'),
            region_name=creds.get('region', 'us-east-1'),
            endpoint_url=creds.get('endpoint_url')
        )
        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName='CPUUtilization',
            StartTime=datetime.utcnow() - timedelta(minutes=5),
            EndTime=datetime.utcnow(),
            Period=300,
            Statistics=['Average']
        )
        datapoints = response.get('Datapoints', [])
        if datapoints:
            datapoints.sort(key=lambda x: x['Timestamp'], reverse=True)
            return {"cpu": datapoints[0]['Average'], "memory": random.uniform(40, 60), "request_load": random.uniform(10, 50), "simulated": False}
        else:
            logger.info("AWS CloudWatch returned no datapoints. Falling back to simulated metrics.")
    except Exception as e:
        logger.warning(f"AWS CloudWatch error: {e}. Falling back to simulated metrics.")
    
    return {"cpu": random.uniform(10, 90), "memory": random.uniform(20, 80), "request_load": random.uniform(5, 100), "simulated": True}

def pull_azure_metrics(creds: dict):
    # Azure Monitor query is complex and requires Resource IDs.
    # Fallback to simulated metrics for now.
    logger.info("Using simulated metrics for Azure fallback.")
    return {"cpu": random.uniform(10, 90), "memory": random.uniform(20, 80), "request_load": random.uniform(5, 100), "simulated": True}

def pull_demo_metrics():
    cpu = _clamp(fetch_prometheus_data(CPU_QUERY), 0.0, 100.0, "cpu_usage")
    memory = _clamp(fetch_prometheus_data(MEMORY_QUERY), 0.0, 100.0, "memory_usage")
    request_load = _clamp(fetch_prometheus_data(REQUEST_QUERY), 0.0, float("inf"), "request_load")
    return {"cpu": cpu, "memory": memory, "request_load": request_load, "simulated": False}

def job():
    db: Session = SessionLocal()
    try:
        users = db.query(User).all()
        for user in users:
            aws_creds = load_user_credentials(user.id, "aws", db)
            azure_creds = load_user_credentials(user.id, "azure", db)
            
            provider = None
            creds = None
            if aws_creds:
                provider = "aws"
                creds = aws_creds
                res = pull_aws_metrics(creds)
            elif azure_creds:
                provider = "azure"
                creds = azure_creds
                res = pull_azure_metrics(creds)
            else:
                provider = "demo"
                res = pull_demo_metrics()
            
            metric = Metrics(
                user_id=user.id,
                cpu_usage=res["cpu"],
                memory_usage=res["memory"],
                request_load=res["request_load"],
                is_simulated=1 if res["simulated"] else 0,
                timestamp=datetime.utcnow()
            )
            db.add(metric)
            db.commit()
            db.refresh(metric)
            
            metrics_dict = {
                "cpu_usage": metric.cpu_usage,
                "memory_usage": metric.memory_usage,
                "request_load": metric.request_load
            }
            
            forecast = _get_forecast(db, user.id)
            run_rl_decision(user.id, metrics_dict, forecast, creds, provider)
            
    except Exception as e:
        logger.error(f"User Metrics job failed: {e}", exc_info=True)
    finally:
        db.close()

def start_scheduler():
    logger.info("Starting per-user metrics collector + RL agent loop (10s interval)")
    schedule.every(10).seconds.do(job)
    while True:
        schedule.run_pending()
        time.sleep(1)
