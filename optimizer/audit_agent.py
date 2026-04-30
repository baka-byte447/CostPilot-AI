import logging

from analyzer.ai_advisor import get_action_explanation
from config import OPTIMIZER_MAX_EXPLANATIONS

logger = logging.getLogger(__name__)


def explain_actions(actions):
    """Attach explainability notes for each optimization action."""
    if not actions:
        return actions

    limit = OPTIMIZER_MAX_EXPLANATIONS
    for idx, action in enumerate(actions):
        if idx >= limit:
            action["explanation"] = _fallback_explanation(action)
            continue

        explanation = _llm_explanation(action)
        if not explanation:
            explanation = _fallback_explanation(action)
        action["explanation"] = explanation

    return actions


def _llm_explanation(action):
    try:
        return get_action_explanation(_action_summary(action))
    except Exception as e:
        logger.debug("LLM explanation failed: %s", e)

    return None


def _fallback_explanation(action):
    return (
        "Action %s for %s %s. Reason: %s. "
        "Risk: verify service dependencies. Rollback: reverse the action if needed."
        % (
            action.get("action"),
            action.get("resource_type"),
            action.get("resource_id"),
            action.get("reason") or "n/a",
        )
    )


def _action_summary(action):
    details = [
        "resource_type=%s" % action.get("resource_type"),
        "resource_id=%s" % action.get("resource_id"),
        "action=%s" % action.get("action"),
    ]
    params = action.get("parameters") or {}
    if params:
        details.append("parameters=%s" % params)
    reason = action.get("reason") or "n/a"
    details.append("reason=%s" % reason)
    return ", ".join(details)
