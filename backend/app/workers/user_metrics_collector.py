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
from app.models.cloud_status_model import CloudResourceStatus
from app.services.metrics_service import fetch_prometheus_data, CPU_QUERY, MEMORY_QUERY, REQUEST_QUERY, _clamp

logger = logging.getLogger(__name__)

_last_explanation_dict = {}
_last_decision_dict = {}

def get_last_explanation(user_id: int) -> dict:
    return _last_explanation_dict.get(user_id)

def get_last_decision(user_id: int) -> dict:
    return _last_decision_dict.get(user_id)

def _get_forecast(db: Session, user_id: int) -> dict:
    try:
        from app.cost.cost_forecast import forecast_cost
        return forecast_cost(db, user_id)
    except Exception as e:
        logger.warning(f"Forecast unavailable for user {user_id}: {e}")
        return {"forecast_available": False}

def run_rl_decision(user_id: int, metrics: dict, forecast: dict = None, creds: dict = None, provider: str = None):
    global _last_explanation_dict
    global _last_decision_dict
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
        _last_decision_dict[user_id] = decision

        if provider == "azure":
            _dispatch_azure(decision, creds)

        return decision

    except Exception as e:
        logger.error(f"RL decision failed for user {user_id}: {e}", exc_info=True)
        return None

def _dispatch_azure(decision: dict, creds: dict = None):
    try:
        from app.optimizer.azure_scaling_executor import azure_executor
        # VMSS-first: scale the user-selected VMSS (if configured).
        vmss_name = (creds or {}).get("vmss_name")
        result = azure_executor.execute(
            {
                "action": decision["action"],
                "resource_type": "vmss",
                "target": {"vmss_name": vmss_name} if vmss_name else {},
                "params": {"increment": 1, "decrement": 1},
            },
            creds,
        )
        if result.get("success"):
            logger.info(f"Azure action applied: {result.get('action')} on VMSS")
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
    from azure.identity import ClientSecretCredential
    from azure.mgmt.compute import ComputeManagementClient
    from azure.mgmt.monitor import MonitorManagementClient
    from datetime import datetime, timedelta, timezone
    from azure.core.exceptions import HttpResponseError, ResourceNotFoundError

    try:
        credential = ClientSecretCredential(
            tenant_id=creds.get("tenant_id", ""),
            client_id=creds.get("client_id", ""),
            client_secret=creds.get("client_secret", "")
        )
        subscription_id = creds.get("subscription_id", "")
        resource_group = creds.get("resource_group", "costpilot-rg")
        vmss_name = creds.get("vmss_name")
        
        compute = ComputeManagementClient(credential, subscription_id)
        monitor = MonitorManagementClient(credential, subscription_id)
        
        if not vmss_name:
            raise ValueError("Azure VMSS not configured: missing vmss_name in saved credentials")

        target_vmss = compute.virtual_machine_scale_sets.get(resource_group, vmss_name)
        resource_id = target_vmss.id
        # NOTE: Azure Monitor expects ISO8601; avoid "+00:00" in query params because "+" can be decoded as space.
        now = datetime.now(timezone.utc)
        start = now - timedelta(minutes=10)
        timespan = f"{start.strftime('%Y-%m-%dT%H:%M:%SZ')}/{now.strftime('%Y-%m-%dT%H:%M:%SZ')}"

        metrics_data = monitor.metrics.list(
            resource_uri=resource_id,
            timespan=timespan,
            interval="PT1M",
            metricnames="Percentage CPU,Network In,Network Out",
            aggregation="Average,Total",
        )

        cpu_val = None
        net_in_total = None

        for metric in metrics_data.value or []:
            if metric.name.value == "Percentage CPU":
                for ts in metric.timeseries or []:
                    for dp in ts.data or []:
                        if getattr(dp, "average", None) is not None:
                            cpu_val = dp.average
            elif metric.name.value == "Network In":
                for ts in metric.timeseries or []:
                    for dp in ts.data or []:
                        if getattr(dp, "total", None) is not None:
                            net_in_total = dp.total

        # VMSS does not provide memory % by default unless guest-level monitoring is enabled.
        mem_val = None
        req_load = (net_in_total / 1024.0) if net_in_total is not None else None

        if cpu_val is None:
            # No datapoints: don't fabricate values; mark degraded upstream.
            return {"cpu": None, "memory": mem_val, "request_load": req_load, "simulated": False, "error": "no_cpu_datapoints"}

        logger.info(
            f"Azure Monitor Metrics [{vmss_name}]: CPU={cpu_val:.2f}%, NetworkInKB={(req_load if req_load is not None else -1):.2f}"
        )
        return {"cpu": cpu_val, "memory": mem_val, "request_load": req_load, "simulated": False}
    except (HttpResponseError, ResourceNotFoundError) as e:
        # Azure unreachable / unauthorized / not found → caller will mark degraded + keep last good metrics.
        return {"cpu": None, "memory": None, "request_load": None, "simulated": True, "error": str(e)}
    except Exception as e:
        return {"cpu": None, "memory": None, "request_load": None, "simulated": True, "error": str(e)}

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
            # Never let a single bad credential blob stop the whole scheduler loop.
            # This commonly happens if ENCRYPTION_KEY changes and older encrypted creds can no longer be decrypted.
            aws_creds = None
            azure_creds = None
            try:
                azure_creds = load_user_credentials(user.id, "azure", db)
            except Exception as e:
                logger.warning(f"Azure credential load failed for user {user.id}: {e}")
            try:
                aws_creds = load_user_credentials(user.id, "aws", db)
            except Exception as e:
                logger.warning(f"AWS credential load failed for user {user.id}: {e}")
            
            provider = None
            creds = None
            if azure_creds:
                provider = "azure"
                creds = azure_creds
                res = pull_azure_metrics(creds)
            elif aws_creds:
                provider = "aws"
                creds = aws_creds
                res = pull_aws_metrics(creds)
            else:
                provider = "demo"
                res = pull_demo_metrics()

            # Update per-user VMSS status (for UI + health signals)
            if provider == "azure":
                status_row = (
                    db.query(CloudResourceStatus)
                    .filter_by(user_id=user.id, provider="azure", resource_type="vmss")
                    .first()
                )
                if status_row:
                    status_row.data_source = "azure_monitor"
                    if res.get("simulated") and res.get("error"):
                        status_row.status = "degraded"
                        status_row.last_metrics_error = res.get("error")
                    elif res.get("error"):
                        status_row.status = "degraded"
                        status_row.last_metrics_error = res.get("error")
                    else:
                        status_row.status = "ok"
                        status_row.last_metrics_error = None
                    db.commit()
            
            # Only persist a new metrics row when we have real signal.
            # For Azure: do NOT write simulated/random values; keep last good metric and surface degraded state via CloudResourceStatus.
            if provider == "azure" and res.get("cpu") is None:
                continue

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

            if provider == "azure":
                status_row = (
                    db.query(CloudResourceStatus)
                    .filter_by(user_id=user.id, provider="azure", resource_type="vmss")
                    .first()
                )
                if status_row:
                    status_row.last_metrics_at = metric.timestamp
                    status_row.last_metrics_error = None if not res.get("error") else res.get("error")
                    status_row.status = "ok" if not res.get("error") else "degraded"
                    db.commit()
            
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
