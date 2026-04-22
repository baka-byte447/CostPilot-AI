import requests
import logging
from sqlalchemy.orm import Session
from app.models.metrics_model import Metrics
from datetime import datetime

logger = logging.getLogger(__name__)

PROMETHEUS_URL = "http://prometheus:9090"
CPU_QUERY = '100 - (avg by(instance)(rate(node_cpu_seconds_total{mode="idle"}[1m])) * 100)'
MEMORY_QUERY = '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100'
REQUEST_QUERY = 'rate(app_requests_total[1m])'


def _clamp(value: float, lo: float, hi: float, name: str) -> float:
    clamped = max(lo, min(hi, value))
    if clamped != value:
        logger.warning(f"Metric '{name}' clamped {value:.4f} -> {clamped:.4f}")
    return clamped


def fetch_prometheus_data(query: str) -> float:
    try:
        response = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={"query": query},
            timeout=5
        )
        data = response.json()
        return float(data["data"]["result"][0]["value"][1])
    except Exception:
        return 0.0


def collect_and_store_metrics(db: Session) -> dict:
    cpu = _clamp(fetch_prometheus_data(CPU_QUERY), 0.0, 100.0, "cpu_usage")
    memory = _clamp(fetch_prometheus_data(MEMORY_QUERY), 0.0, 100.0, "memory_usage")
    request_load = _clamp(fetch_prometheus_data(REQUEST_QUERY), 0.0, float("inf"), "request_load")

    metric = Metrics(
        cpu_usage=cpu,
        memory_usage=memory,
        request_load=request_load,
        timestamp=datetime.utcnow()
    )
    db.add(metric)
    db.commit()
    db.refresh(metric)

    return {
        "cpu_usage": cpu,
        "memory_usage": memory,
        "request_load": request_load,
        "timestamp": metric.timestamp
    }


def get_all_metrics(db: Session):
    return db.query(Metrics).all()
