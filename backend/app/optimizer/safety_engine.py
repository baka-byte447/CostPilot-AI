import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class SLOConfig:
    max_cpu_pct: float = 85.0
    max_memory_pct: float = 90.0
    max_request_load: float = 2.0
    min_replicas: int = 1
    max_replicas: int = 8
    max_scale_step: int = 2
    min_cpu_to_scale_down: float = 0.0
    max_cpu_to_scale_down: float = 40.0
    max_memory_to_scale_down: float = 50.0
    max_requests_to_scale_down: float = 0.3
    cooldown_seconds: int = 30

_last_action_time: float = 0.0
_last_replicas: int = 2

SLO = SLOConfig(
    max_cpu_pct=float(os.getenv("SLO_MAX_CPU", 85)),
    max_memory_pct=float(os.getenv("SLO_MAX_MEMORY", 90)),
    max_request_load=float(os.getenv("SLO_MAX_REQUESTS", 2.0)),
    min_replicas=int(os.getenv("SLO_MIN_REPLICAS", 1)),
    max_replicas=int(os.getenv("SLO_MAX_REPLICAS", 8)),
    max_scale_step=int(os.getenv("SLO_MAX_SCALE_STEP", 2)),
    cooldown_seconds=int(os.getenv("SLO_COOLDOWN_SECONDS", 30)),
)


def check_action(
    proposed_action: str,
    current_replicas: int,
    cpu: float,
    memory: float,
    request_load: float
) -> dict:
    global _last_action_time, _last_replicas

    violations = []
    safe_action = proposed_action
    blocked = False

    now = time.time()
    seconds_since_last = now - _last_action_time

    if proposed_action in ("scale_up", "scale_down") and seconds_since_last < SLO.cooldown_seconds:
        violations.append(
            f"Cooldown active — {SLO.cooldown_seconds - int(seconds_since_last)}s remaining"
        )
        safe_action = "maintain"
        blocked = True

    if proposed_action == "scale_up":
        new_replicas = min(current_replicas + 1, SLO.max_replicas)
        if new_replicas == SLO.max_replicas and current_replicas == SLO.max_replicas:
            violations.append(f"Already at max replicas ({SLO.max_replicas})")
            safe_action = "maintain"
            blocked = True

    if proposed_action == "scale_down":
        new_replicas = max(current_replicas - 1, SLO.min_replicas)

        if new_replicas == SLO.min_replicas and current_replicas == SLO.min_replicas:
            violations.append(f"Already at min replicas ({SLO.min_replicas})")
            safe_action = "maintain"
            blocked = True

        if cpu > SLO.max_cpu_to_scale_down:
            violations.append(f"CPU {cpu:.1f}% too high to scale down (threshold: {SLO.max_cpu_to_scale_down}%)")
            safe_action = "maintain"
            blocked = True

        if memory > SLO.max_memory_to_scale_down:
            violations.append(f"Memory {memory:.1f}% too high to scale down (threshold: {SLO.max_memory_to_scale_down}%)")
            safe_action = "maintain"
            blocked = True

        if request_load > SLO.max_requests_to_scale_down:
            violations.append(f"Request load {request_load:.3f} too high to scale down (threshold: {SLO.max_requests_to_scale_down})")
            safe_action = "maintain"
            blocked = True

    if cpu > SLO.max_cpu_pct and proposed_action == "scale_down":
        violations.append(f"SLO breach — CPU {cpu:.1f}% exceeds {SLO.max_cpu_pct}%")
        safe_action = "scale_up"
        blocked = True

    if memory > SLO.max_memory_pct and proposed_action == "scale_down":
        violations.append(f"SLO breach — Memory {memory:.1f}% exceeds {SLO.max_memory_pct}%")
        safe_action = "scale_up"
        blocked = True

    if request_load > SLO.max_request_load and proposed_action == "scale_down":
        violations.append(f"SLO breach — Request load {request_load:.3f} exceeds {SLO.max_request_load}")
        safe_action = "scale_up"
        blocked = True

    if not blocked and proposed_action in ("scale_up", "scale_down"):
        _last_action_time = now

    if violations:
        logger.warning(f"Safety engine: {len(violations)} violation(s) — action {proposed_action} → {safe_action}")
        for v in violations:
            logger.warning(f"  ✗ {v}")
    else:
        logger.info(f"Safety engine: action {proposed_action} approved")

    return {
        "proposed_action": proposed_action,
        "safe_action": safe_action,
        "blocked": blocked,
        "violations": violations,
        "slo_status": {
            "cpu_ok":     cpu <= SLO.max_cpu_pct,
            "memory_ok":  memory <= SLO.max_memory_pct,
            "requests_ok": request_load <= SLO.max_request_load,
        }
    }


def clamp_replicas(current: int, proposed: int) -> int:
    proposed = max(SLO.min_replicas, min(SLO.max_replicas, proposed))
    if abs(proposed - current) > SLO.max_scale_step:
        proposed = current + SLO.max_scale_step if proposed > current else current - SLO.max_scale_step
    return proposed


def record_replicas(replicas: int) -> None:
    global _last_replicas
    _last_replicas = replicas


def get_last_replicas() -> int:
    return _last_replicas


def get_slo_config() -> dict:
    return {
        "max_cpu_pct": SLO.max_cpu_pct,
        "max_memory_pct": SLO.max_memory_pct,
        "max_request_load": SLO.max_request_load,
        "min_replicas": SLO.min_replicas,
        "max_replicas": SLO.max_replicas,
        "max_scale_step": SLO.max_scale_step,
        "cooldown_seconds": SLO.cooldown_seconds,
        "max_cpu_to_scale_down": SLO.max_cpu_to_scale_down,
        "max_memory_to_scale_down": SLO.max_memory_to_scale_down,
        "max_requests_to_scale_down": SLO.max_requests_to_scale_down,
    }


def get_safety_status() -> dict:
    now = time.time()
    seconds_since_last = now - _last_action_time
    remaining = max(0, SLO.cooldown_seconds - int(seconds_since_last)) if _last_action_time else 0
    last_action = None
    if _last_action_time:
        last_action = datetime.utcfromtimestamp(_last_action_time).isoformat() + "Z"

    return {
        "cooldown_active": remaining > 0,
        "cooldown_remaining": remaining,
        "last_action_time": last_action,
        "circuit_breaker": "CLOSED",
    }