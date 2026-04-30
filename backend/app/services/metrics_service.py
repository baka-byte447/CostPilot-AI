import logging
import math
import random
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import requests
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.models.metrics_model import Metrics


logger = logging.getLogger(__name__)

CPU_QUERY = '100 - (avg by(instance)(rate(node_cpu_seconds_total{mode="idle"}[1m])) * 100)'
MEMORY_QUERY = "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes))* 100"
REQUEST_QUERY = "rate(app_requests_total[1m])"

# ── Prometheus fetcher ──────────────────────────────────────────────

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


# ── Realistic metrics simulator ─────────────────────────────────────

_prometheus_status = {"available": None, "last_checked": 0.0}

def _check_prometheus() -> bool:
    """TTL-based check to see if Prometheus is reachable."""
    now = time.time()
    if _prometheus_status["available"] is not None and (now - _prometheus_status["last_checked"] < 60.0):
        return _prometheus_status["available"]
        
    try:
        r = requests.get(f"{settings.prometheus_url}/-/ready", timeout=2)
        _prometheus_status["available"] = r.status_code == 200
    except Exception:
        _prometheus_status["available"] = False
        
    _prometheus_status["last_checked"] = now
    if not _prometheus_status["available"]:
        logger.info(
            "Prometheus not available — switching to simulated metrics mode"
        )
    return _prometheus_status["available"]


def _simulate_metrics() -> Dict[str, float]:
    """Generate realistic-looking infrastructure metrics.

    Uses a combination of:
      - Time-of-day sine wave (simulates daily load pattern)
      - Random walk component (simulates organic traffic spikes)
      - Gaussian noise (simulates real-world jitter)
    """
    t = time.time()

    # Base sine wave: peaks during "business hours"
    hour_cycle = math.sin(t / 3600 * math.pi)  # ~2h full cycle for demo
    minute_ripple = math.sin(t / 120 * math.pi) * 0.15  # 2-min micro-cycle

    # CPU: 25-75% base range with spikes
    cpu_base = 35 + 20 * hour_cycle + 10 * minute_ripple
    cpu_noise = random.gauss(0, 4)
    cpu_spike = random.random() * 15 if random.random() < 0.1 else 0  # 10% chance of spike
    cpu = max(5.0, min(95.0, cpu_base + cpu_noise + cpu_spike))

    # Memory: generally higher and more stable than CPU (40-80%)
    mem_base = 52 + 15 * hour_cycle + 5 * minute_ripple
    mem_noise = random.gauss(0, 2.5)
    memory = max(20.0, min(92.0, mem_base + mem_noise))

    # Requests/sec: 0.2-3.0 range, correlated with CPU
    req_base = 0.8 + 1.2 * ((cpu - 30) / 60)
    req_noise = random.gauss(0, 0.15)
    req_spike = random.random() * 1.5 if random.random() < 0.08 else 0
    request_load = max(0.05, min(5.0, req_base + req_noise + req_spike))

    return {
        "cpu_usage": round(cpu, 2),
        "memory_usage": round(memory, 2),
        "request_load": round(request_load, 3),
    }


# ── Public API ──────────────────────────────────────────────────────

def collect_and_store_metrics(db: Session, user_id: str = "system") -> Dict[str, Any]:
    """Collect CPU, memory, and request rate metrics and persist them.

    Uses Prometheus when available; falls back to realistic simulation
    when settings.simulate_metrics is True and Prometheus is unreachable.
    """
    use_simulation = settings.simulate_metrics and not _check_prometheus()

    if use_simulation:
        data = _simulate_metrics()
        cpu = data["cpu_usage"]
        memory = data["memory_usage"]
        requests_per_sec = data["request_load"]
    else:
        cpu = fetch_prometheus_data(CPU_QUERY)
        memory = fetch_prometheus_data(MEMORY_QUERY)
        requests_per_sec = fetch_prometheus_data(REQUEST_QUERY)

    metric = Metrics(
        user_id=user_id,
        cpu_usage=cpu,
        memory_usage=memory,
        request_load=requests_per_sec,
        timestamp=datetime.now(timezone.utc),
    )

    db.add(metric)
    db.commit()
    db.refresh(metric)

    return {
        "cpu_usage": cpu,
        "memory_usage": memory,
        "request_load": requests_per_sec,
        "timestamp": metric.timestamp,
    }


def get_all_metrics(db: Session, user_id: str, limit: int = 100, hours: int = 24):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    return db.query(Metrics).filter(Metrics.user_id == user_id, Metrics.timestamp >= cutoff).order_by(Metrics.timestamp.desc()).limit(limit).all()
