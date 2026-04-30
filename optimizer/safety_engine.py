from datetime import datetime, timezone

from config import (
    SLO_COOLDOWN_SECONDS,
    SLO_MAX_CPU,
    SLO_MAX_MEMORY,
    SLO_MAX_REQUESTS,
    SLO_MAX_REPLICAS,
    SLO_MIN_REPLICAS,
)


def enforce_slo_guardrails(resource, decision, latest_action):
    """
    Apply SLO guardrails to RL decisions.
    Returns: (decision, safe, safety_note)
    """
    action = decision.get("action", "maintain")
    cpu = float(decision.get("cpu", 0.0))
    memory = float(decision.get("memory", 0.0))
    request_load = float(decision.get("request_load", 0.0))

    if _in_cooldown(latest_action):
        return "maintain", False, "cooldown_active"

    # High pressure must avoid downscaling.
    if cpu > SLO_MAX_CPU or memory > SLO_MAX_MEMORY or request_load > SLO_MAX_REQUESTS:
        if action == "scale_down":
            return "maintain", False, "blocked_by_slo_pressure"
        return action, True, "high_pressure_ok"

    # Very low utilization allows downscale, but do not force beyond min replicas.
    if action == "scale_down" and not _can_scale_down(resource):
        return "maintain", False, "min_replicas_reached"

    if action == "scale_up" and not _can_scale_up(resource):
        return "maintain", False, "max_replicas_reached"

    return action, True, "within_slo_bounds"


def _in_cooldown(latest_action):
    if not latest_action:
        return False
    applied_at = latest_action.get("applied_at") or latest_action.get("created_at")
    if not applied_at:
        return False
    try:
        then = datetime.fromisoformat(applied_at.replace("Z", "+00:00"))
        if then.tzinfo is None:
            then = then.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        return (now - then).total_seconds() < SLO_COOLDOWN_SECONDS
    except Exception:
        return False


def _can_scale_down(resource):
    replicas = int(resource.get("replicas", 1) or 1)
    return replicas > SLO_MIN_REPLICAS


def _can_scale_up(resource):
    replicas = int(resource.get("replicas", 1) or 1)
    return replicas < SLO_MAX_REPLICAS
