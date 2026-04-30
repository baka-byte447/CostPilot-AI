import logging

from config import (
    OPTIMIZER_CPU_LOW_PCT,
    OPTIMIZER_CPU_HIGH_PCT,
    OPTIMIZER_ALLOW_EC2_STOP,
    OPTIMIZER_ALLOW_EC2_RESIZE,
    OPTIMIZER_ALLOW_RDS_STOP,
    OPTIMIZER_MIN_CONFIDENCE,
)
from optimizer.safety_engine import enforce_slo_guardrails

logger = logging.getLogger(__name__)


_INSTANCE_DOWNSIZE_MAP = {
    "t3.large": "t3.medium",
    "t3.medium": "t3.small",
    "t3.small": "t3.micro",
    "t3.micro": "t3.nano",
    "t3a.large": "t3a.medium",
    "t3a.medium": "t3a.small",
    "t3a.small": "t3a.micro",
}

_EC2_HOURLY_COST = {
    "t3.large": 0.0832,
    "t3.medium": 0.0416,
    "t3.small": 0.0208,
    "t3.micro": 0.0104,
    "t3.nano": 0.0052,
    "t3a.large": 0.0752,
    "t3a.medium": 0.0376,
    "t3a.small": 0.0188,
    "t3a.micro": 0.0094,
}


def recommend_actions(resources, metrics, forecasts, findings=None, rl_decisions=None, latest_action_index=None):
    """Create optimization actions using RL decisions with heuristic fallbacks."""
    metric_index = _index_metrics(metrics)
    forecast_index = _index_forecasts(forecasts)
    rl_index = _index_rl_decisions(rl_decisions)
    latest_action_index = latest_action_index or {}
    actions = []

    if findings:
        actions.extend(_actions_from_findings(findings))

    for r in resources or []:
        r_type = r.get("type") or r.get("resource_type") or "Unknown"
        if r_type == "EC2":
            action = _recommend_ec2_action(r, metric_index, forecast_index, rl_index, latest_action_index)
        elif r_type == "RDS":
            action = _recommend_rds_action(r, metric_index, forecast_index, rl_index, latest_action_index)
        else:
            action = None

        if action:
            actions.append(action)

    deduped = _dedupe_actions(actions)
    logger.info("Recommended %d optimization actions", len(deduped))
    return deduped


def _index_metrics(metrics):
    index = {}
    for series in metrics or []:
        index[(series.resource_id, series.metric_name)] = series
    return index


def _index_forecasts(forecasts):
    index = {}
    for fc in forecasts or []:
        index[(fc.resource_id, fc.metric_name)] = fc
    return index


def _index_rl_decisions(rl_decisions):
    index = {}
    for d in rl_decisions or []:
        index[d.resource_id] = d
    return index


def _recommend_ec2_action(resource, metric_index, forecast_index, rl_index, latest_action_index):
    status = (resource.get("status") or "").lower()
    if status not in ("running", "active"):
        return None

    instance_id = resource.get("id") or resource.get("resource_id")
    cpu_series = metric_index.get((instance_id, "CPUUtilization"))
    cpu_forecast = forecast_index.get((instance_id, "CPUUtilization"))

    if not cpu_series or not cpu_forecast:
        return None

    avg_cpu = cpu_series.avg_value
    pred_cpu = cpu_forecast.predicted_avg

    rl = rl_index.get(instance_id)
    if rl:
        latest_action = latest_action_index.get(instance_id)
        safe_action, safe, safety_note = enforce_slo_guardrails(
            resource,
            {"action": rl.action, "cpu": rl.cpu, "memory": rl.memory, "request_load": rl.request_load},
            latest_action,
        )
        if safe_action == "maintain":
            return _build_action(
                resource,
                action="maintain",
                reason="RL chose maintain (%s) at cpu %.1f%% mem %.1f%% req %.2f"
                % (safety_note, rl.cpu, rl.memory, rl.request_load),
                confidence=max(OPTIMIZER_MIN_CONFIDENCE, rl.confidence),
                parameters={
                    "rl_decision": rl.action,
                    "state_idx": rl.state_idx,
                    "q_values": rl.q_values,
                    "safe": safe,
                    "safety_note": safety_note,
                    "manual_only": True,
                },
                estimated_savings=0.0,
            )
        if safe_action == "scale_down":
            return _scale_down_action(resource, avg_cpu, pred_cpu, rl, safety_note)
        if safe_action == "scale_up":
            return _scale_up_action(resource, avg_cpu, pred_cpu, rl, safety_note)

    if avg_cpu < OPTIMIZER_CPU_LOW_PCT and pred_cpu < OPTIMIZER_CPU_LOW_PCT:
        instance_type = _get_instance_type(resource)
        new_type = _downsize_instance(instance_type)
        confidence = _confidence_low(avg_cpu, OPTIMIZER_CPU_LOW_PCT)
        reason = (
            "Avg CPU %.1f%% and forecast %.1f%% are below %.1f%%"
            % (avg_cpu, pred_cpu, OPTIMIZER_CPU_LOW_PCT)
        )

        if OPTIMIZER_ALLOW_EC2_RESIZE and new_type:
            return _build_action(
                resource,
                action="resize",
                reason=reason,
                confidence=confidence,
                parameters={
                    "from_type": instance_type,
                    "to_type": new_type,
                    "restart": True,
                },
                estimated_savings=_estimate_resize_savings(instance_type, new_type),
            )

        if OPTIMIZER_ALLOW_EC2_STOP:
            return _build_action(
                resource,
                action="stop",
                reason=reason,
                confidence=confidence,
                parameters={},
                estimated_savings=0.0,
            )

    if avg_cpu > OPTIMIZER_CPU_HIGH_PCT or pred_cpu > OPTIMIZER_CPU_HIGH_PCT:
        confidence = _confidence_high(max(avg_cpu, pred_cpu), OPTIMIZER_CPU_HIGH_PCT)
        reason = (
            "Avg CPU %.1f%% or forecast %.1f%% exceed %.1f%%"
            % (avg_cpu, pred_cpu, OPTIMIZER_CPU_HIGH_PCT)
        )
        instance_type = _get_instance_type(resource)
        up_type = _upsize_instance(instance_type)
        if up_type:
            return _build_action(
                resource,
                action="resize",
                reason=reason,
                confidence=confidence,
                parameters={
                    "from_type": instance_type,
                    "to_type": up_type,
                    "restart": True,
                    "manual_only": True,
                },
                estimated_savings=0.0,
            )

    return None


def _recommend_rds_action(resource, metric_index, forecast_index, rl_index, latest_action_index):
    status = (resource.get("status") or "").lower()
    if status not in ("available", "running"):
        return None

    db_id = resource.get("id") or resource.get("resource_id")
    cpu_series = metric_index.get((db_id, "CPUUtilization"))
    cpu_forecast = forecast_index.get((db_id, "CPUUtilization"))
    if not cpu_series or not cpu_forecast:
        return None

    avg_cpu = cpu_series.avg_value
    pred_cpu = cpu_forecast.predicted_avg

    rl = rl_index.get(db_id)
    if rl:
        latest_action = latest_action_index.get(db_id)
        safe_action, safe, safety_note = enforce_slo_guardrails(
            resource,
            {"action": rl.action, "cpu": rl.cpu, "memory": rl.memory, "request_load": rl.request_load},
            latest_action,
        )
        if safe_action == "maintain":
            return _build_action(
                resource,
                action="maintain",
                reason="RL chose maintain (%s) at cpu %.1f%% mem %.1f%% req %.2f"
                % (safety_note, rl.cpu, rl.memory, rl.request_load),
                confidence=max(OPTIMIZER_MIN_CONFIDENCE, rl.confidence),
                parameters={
                    "rl_decision": rl.action,
                    "state_idx": rl.state_idx,
                    "q_values": rl.q_values,
                    "safe": safe,
                    "safety_note": safety_note,
                    "manual_only": True,
                },
                estimated_savings=0.0,
            )

    if avg_cpu < OPTIMIZER_CPU_LOW_PCT and pred_cpu < OPTIMIZER_CPU_LOW_PCT and OPTIMIZER_ALLOW_RDS_STOP:
        confidence = _confidence_low(avg_cpu, OPTIMIZER_CPU_LOW_PCT)
        reason = (
            "Avg CPU %.1f%% and forecast %.1f%% are below %.1f%%"
            % (avg_cpu, pred_cpu, OPTIMIZER_CPU_LOW_PCT)
        )
        return _build_action(
            resource,
            action="stop",
            reason=reason,
            confidence=confidence,
            parameters={},
            estimated_savings=0.0,
        )
    return None


def _scale_down_action(resource, avg_cpu, pred_cpu, rl, safety_note):
    instance_type = _get_instance_type(resource)
    new_type = _downsize_instance(instance_type)
    confidence = max(_confidence_low(avg_cpu, OPTIMIZER_CPU_LOW_PCT), rl.confidence)
    reason = "RL scale_down (%s): cpu %.1f%% forecast %.1f%%" % (safety_note, avg_cpu, pred_cpu)
    if OPTIMIZER_ALLOW_EC2_RESIZE and new_type:
        return _build_action(
            resource,
            action="resize",
            reason=reason,
            confidence=confidence,
            parameters={
                "from_type": instance_type,
                "to_type": new_type,
                "restart": True,
                "rl_decision": "scale_down",
                "state_idx": rl.state_idx,
                "q_values": rl.q_values,
                "safety_note": safety_note,
            },
            estimated_savings=_estimate_resize_savings(instance_type, new_type),
        )
    if OPTIMIZER_ALLOW_EC2_STOP:
        return _build_action(
            resource,
            action="stop",
            reason=reason,
            confidence=confidence,
            parameters={
                "rl_decision": "scale_down",
                "state_idx": rl.state_idx,
                "q_values": rl.q_values,
                "safety_note": safety_note,
            },
            estimated_savings=0.0,
        )
    return None


def _scale_up_action(resource, avg_cpu, pred_cpu, rl, safety_note):
    confidence = max(_confidence_high(max(avg_cpu, pred_cpu), OPTIMIZER_CPU_HIGH_PCT), rl.confidence)
    reason = "RL scale_up (%s): cpu %.1f%% forecast %.1f%%" % (safety_note, avg_cpu, pred_cpu)
    instance_type = _get_instance_type(resource)
    up_type = _upsize_instance(instance_type)
    if up_type:
        return _build_action(
            resource,
            action="resize",
            reason=reason,
            confidence=confidence,
            parameters={
                "from_type": instance_type,
                "to_type": up_type,
                "restart": True,
                "manual_only": True,
                "rl_decision": "scale_up",
                "state_idx": rl.state_idx,
                "q_values": rl.q_values,
                "safety_note": safety_note,
            },
            estimated_savings=0.0,
        )
    return _build_action(
        resource,
        action="maintain",
        reason=reason,
        confidence=confidence,
        parameters={
            "rl_decision": "scale_up",
            "state_idx": rl.state_idx,
            "q_values": rl.q_values,
            "safety_note": safety_note,
            "manual_only": True,
        },
        estimated_savings=0.0,
    )


def _actions_from_findings(findings):
    actions = []
    for f in findings:
        f_type = f.get("type") or f.get("resource_type") or "Unknown"
        resource_id = f.get("id") or f.get("resource_id")
        region = f.get("region")
        waste = float(f.get("waste_usd") or 0.0)

        if f_type in ("EBS", "ElasticIP", "Snapshot"):
            actions.append(
                {
                    "resource_id": resource_id,
                    "resource_type": f_type,
                    "region": region,
                    "action": "delete",
                    "parameters": {},
                    "reason": f.get("detail") or "Unused resource detected",
                    "confidence": 0.8,
                    "estimated_savings": waste,
                }
            )
        elif f_type in ("Idle EC2", "Stopped EC2"):
            manual_only = not OPTIMIZER_ALLOW_EC2_STOP
            actions.append(
                {
                    "resource_id": resource_id,
                    "resource_type": "EC2",
                    "region": region,
                    "action": "stop",
                    "parameters": {"manual_only": manual_only} if manual_only else {},
                    "reason": f.get("detail") or "Idle EC2 detected",
                    "confidence": 0.6,
                    "estimated_savings": waste,
                }
            )

    return actions


def _build_action(resource, action, reason, confidence, parameters, estimated_savings):
    if confidence < OPTIMIZER_MIN_CONFIDENCE:
        return None

    return {
        "resource_id": resource.get("id") or resource.get("resource_id"),
        "resource_type": resource.get("type") or resource.get("resource_type"),
        "region": resource.get("region"),
        "action": action,
        "parameters": parameters,
        "reason": reason,
        "confidence": round(confidence, 3),
        "estimated_savings": round(float(estimated_savings), 2),
    }


def _dedupe_actions(actions):
    priority = {"delete": 4, "stop": 3, "resize": 2, "maintain": 1}
    best = {}

    for action in actions:
        rid = action.get("resource_id")
        if not rid:
            continue
        current = best.get(rid)
        if not current:
            best[rid] = action
            continue
        if priority.get(action.get("action"), 0) > priority.get(current.get("action"), 0):
            best[rid] = action

    return list(best.values())


def _get_instance_type(resource):
    if resource.get("instance_type"):
        return resource.get("instance_type")

    detail = resource.get("detail") or ""
    if " - " in detail:
        return detail.split(" - ", 1)[0].strip()
    return detail.split()[0] if detail else None


def _downsize_instance(instance_type):
    if not instance_type:
        return None
    return _INSTANCE_DOWNSIZE_MAP.get(instance_type)


def _upsize_instance(instance_type):
    if not instance_type:
        return None
    reverse_map = {v: k for k, v in _INSTANCE_DOWNSIZE_MAP.items()}
    return reverse_map.get(instance_type)


def _estimate_resize_savings(old_type, new_type):
    if not old_type or not new_type:
        return 0.0
    old_cost = _EC2_HOURLY_COST.get(old_type)
    new_cost = _EC2_HOURLY_COST.get(new_type)
    if old_cost is None or new_cost is None:
        return 0.0
    return (old_cost - new_cost) * 24 * 30


def _confidence_low(value, threshold):
    if value is None:
        return 0.0
    if value >= threshold:
        return 0.4
    return min(0.95, 0.5 + (threshold - value) / threshold * 0.5)


def _confidence_high(value, threshold):
    if value is None:
        return 0.0
    if value <= threshold:
        return 0.4
    return min(0.95, 0.5 + (value - threshold) / threshold * 0.5)
