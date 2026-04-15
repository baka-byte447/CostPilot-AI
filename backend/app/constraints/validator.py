"""Constraint enforcement and SLA/SLO validation."""

from typing import Any, Dict, Optional, Tuple


class ConstraintManager:
    """Enforces SLA/SLO constraints on scaling decisions."""

    def __init__(self, budget_limit: Optional[float] = None, min_replicas: int = 1, max_replicas: int = 50):
        self.sla_rules = {"latency_ms": 250, "error_rate": 0.02}
        self.budget_limit = budget_limit
        self.min_replicas = min_replicas
        self.max_replicas = max_replicas

    def validate_action(self, action: Dict[str, Any], state: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if an action violates constraint boundaries."""
        replicas = action.get("replicas")
        est_cost = action.get("estimated_cost")

        if replicas is not None:
            if replicas < self.min_replicas:
                return False, f"replicas below minimum ({self.min_replicas})"
            if replicas > self.max_replicas:
                return False, f"replicas above maximum ({self.max_replicas})"

        if self.budget_limit is not None and est_cost is not None and est_cost > self.budget_limit:
            return False, "budget limit exceeded"

        sla_violation = self.check_sla_violation(state)
        if sla_violation:
            return False, sla_violation

        return True, "ok"

    def check_sla_violation(self, metrics: Dict[str, Any]) -> str:
        """Check if current metrics violate any SLA."""
        latency = metrics.get("latency_ms")
        error_rate = metrics.get("error_rate")

        if latency is not None and latency > self.sla_rules["latency_ms"]:
            return f"latency {latency}ms over target {self.sla_rules['latency_ms']}ms"
        if error_rate is not None and error_rate > self.sla_rules["error_rate"]:
            return f"error rate {error_rate:.3f} over target {self.sla_rules['error_rate']}"
        return ""

    def adjust_action_safely(self, action: Dict[str, Any], constraints: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Adjust an action to comply with configured constraints."""
        min_replicas = constraints.get("min_replicas", self.min_replicas) if constraints else self.min_replicas
        max_replicas = constraints.get("max_replicas", self.max_replicas) if constraints else self.max_replicas

        updated = dict(action)
        replicas = updated.get("replicas")
        if replicas is not None:
            updated["replicas"] = max(min_replicas, min(max_replicas, replicas))
        return updated
