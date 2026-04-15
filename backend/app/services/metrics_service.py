import logging
from datetime import datetime
from typing import Any, Dict

import requests
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.models.metrics_model import Metrics


logger = logging.getLogger(__name__)

CPU_QUERY = '100 - (avg by(instance)(rate(node_cpu_seconds_total{mode="idle"}[1m])) * 100)'
MEMORY_QUERY = "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes))* 100"
REQUEST_QUERY = "rate(app_requests_total[1m])"


def fetch_prometheus_data(query: str) -> float:
    """Run a PromQL query and return the numeric result or 0.0 on failure."""
    try:
        response = requests.get(
            f"{settings.prometheus_url}/api/v1/query",
            params={"query": query},
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
        return float(data["data"]["result"][0]["value"][1])
    except Exception as exc:  # pragma: no cover - network dependent
        logger.warning("Prometheus query failed for %s: %s", query, exc)
        return 0.0


def collect_and_store_metrics(db: Session) -> Dict[str, Any]:
    """Collect CPU, memory, and request rate metrics from Prometheus and persist them."""
    cpu = fetch_prometheus_data(CPU_QUERY)
    memory = fetch_prometheus_data(MEMORY_QUERY)
    requests_per_sec = fetch_prometheus_data(REQUEST_QUERY)

    metric = Metrics(cpu_usage=cpu, memory_usage=memory, request_load=requests_per_sec, timestamp=datetime.utcnow())

    db.add(metric)
    db.commit()
    db.refresh(metric)

    return {
        "cpu_usage": cpu,
        "memory_usage": memory,
        "request_load": requests_per_sec,
        "timestamp": metric.timestamp,
    }


def get_all_metrics(db: Session):
    return db.query(Metrics).order_by(Metrics.timestamp.desc()).all()

