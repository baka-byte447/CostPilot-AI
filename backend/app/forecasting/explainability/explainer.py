"""Explainability helpers that generate human-readable summaries."""

from typing import Any, Dict, Iterable, List


class ExplainabilityEngine:
    """Generates natural language explanations for actions."""

    def __init__(self, use_llm: bool = False):
        self.use_llm = use_llm

    def explain_action(self, action: Dict[str, Any], state: Dict[str, Any], forecast: Dict[str, Any], reward: float) -> str:
        """Create a concise, human-readable justification for an action."""
        action_desc = action.get("description") or f"scale to {action.get('replicas', '?')} replicas"
        cpu = state.get("cpu") or forecast.get("cpu")
        mem = state.get("memory") or forecast.get("memory")
        load = state.get("requests") or forecast.get("requests")

        reasons: List[str] = []
        if cpu is not None:
            reasons.append(f"CPU trending at {cpu:.1f}%")
        if mem is not None:
            reasons.append(f"memory near {mem:.1f}%")
        if load is not None:
            reasons.append(f"load forecast {load:.0f} rps")

        if not reasons:
            reasons.append("baseline policy applied")

        reward_note = f"expected reward {reward:.2f}" if reward is not None else "reward not evaluated"
        return f"Chose to {action_desc} because {', '.join(reasons)} ({reward_note})."

    def explain_constraint_violation(self, action: Dict[str, Any], violated_constraint: str) -> str:
        """Explain why an action was blocked due to constraints."""
        action_desc = action.get("description") or action.get("type", "action")
        return f"Blocked {action_desc} because it violates {violated_constraint}."

    def generate_audit_summary(self, action_log: Iterable[Dict[str, Any]]) -> str:
        """Generate a short summary of the latest decisions."""
        entries = list(action_log)
        if not entries:
            return "No audit entries recorded yet."

        latest = entries[-5:]
        lines = [
            f"{item.get('timestamp', '?')}: {item.get('action', 'unknown')} -> replicas {item.get('replicas', '?')} (reward {item.get('reward', '?')})"
            for item in latest
        ]
        return "\n".join(lines)
