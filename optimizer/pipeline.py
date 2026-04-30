import logging

from config import (
    AUTO_APPLY_OPTIMIZATIONS,
    OPTIMIZER_LOOKBACK_DAYS,
    OPTIMIZER_FORECAST_HORIZON_HOURS,
    OPTIMIZER_MAX_RESOURCES,
    OPTIMIZER_METRIC_PERIOD,
)
from data_source import get_active_services, get_findings
from db.database import (
    setup_db,
    save_metrics,
    save_forecasts,
    save_optimizations,
    update_optimization_status,
    update_optimization_explanation,
    get_latest_optimization_by_resource,
)
from optimizer.audit_agent import explain_actions
from optimizer.deployment_agent import apply_actions
from optimizer.forecasting import forecast_metrics
from optimizer.optimization_agent import recommend_actions
from optimizer.rl_agent import build_rl_decisions
from optimizer.usage_monitor import collect_metrics

logger = logging.getLogger(__name__)


def run_autonomous_optimizer(
    auto_apply=False,
    lookback_days=None,
    horizon_hours=None,
    max_resources=None,
    include_findings=True,
):
    """Run the full monitoring, forecasting, optimization, and deployment flow."""
    setup_db()

    lookback_days = lookback_days or OPTIMIZER_LOOKBACK_DAYS
    horizon_hours = horizon_hours or OPTIMIZER_FORECAST_HORIZON_HOURS
    max_resources = max_resources or OPTIMIZER_MAX_RESOURCES

    resources = get_active_services()
    findings = get_findings() if include_findings else []

    metrics = collect_metrics(
        resources,
        lookback_days=lookback_days,
        period_seconds=OPTIMIZER_METRIC_PERIOD,
        max_resources=max_resources,
    )
    save_metrics(metrics)

    forecasts = forecast_metrics(metrics, horizon_hours=horizon_hours)
    save_forecasts(forecasts)

    rl_decisions = build_rl_decisions(resources, metrics, forecasts)
    latest_action_index = _latest_action_index(resources)
    actions = recommend_actions(
        resources,
        metrics,
        forecasts,
        findings,
        rl_decisions=rl_decisions,
        latest_action_index=latest_action_index,
    )
    save_optimizations(actions)

    explain_actions(actions)
    for action in actions:
        if action.get("explanation") and action.get("id"):
            update_optimization_explanation(action["id"], action["explanation"])

    applied_results = []
    if auto_apply or AUTO_APPLY_OPTIMIZATIONS:
        applied_results = apply_actions(actions)
        for result in applied_results:
            update_optimization_status(
                result.get("action_id"),
                result.get("status"),
                result.get("message"),
                applied_at=result.get("applied_at"),
            )

    summary = {
        "resources": len(resources or []),
        "findings": len(findings or []),
        "metrics": len(metrics or []),
        "forecasts": len(forecasts or []),
        "actions": len(actions or []),
        "rl_decisions": len(rl_decisions or []),
        "scale_up": len([d for d in rl_decisions if d.action == "scale_up"]),
        "maintain": len([d for d in rl_decisions if d.action == "maintain"]),
        "scale_down": len([d for d in rl_decisions if d.action == "scale_down"]),
        "applied": len([r for r in applied_results if r.get("status") == "applied"]),
    }

    logger.info("Optimizer summary: %s", summary)
    return summary


def _latest_action_index(resources):
    index = {}
    for resource in resources or []:
        rid = resource.get("id") or resource.get("resource_id")
        if not rid:
            continue
        latest = get_latest_optimization_by_resource(rid)
        if latest:
            index[rid] = latest
    return index
