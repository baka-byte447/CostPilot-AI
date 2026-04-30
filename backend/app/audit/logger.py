"""Lightweight audit trail for scaling decisions."""

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional


class AuditLogger:
    """Append-only audit trail for decisions and their execution results."""

    def __init__(self):
        self._entries: List[Dict[str, Any]] = []

    def log_decision(self, state: Dict[str, Any], action: Dict[str, Any], forecast: Dict[str, Any], reward: Optional[float]) -> Dict[str, Any]:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "decision",
            "state": state,
            "action": action,
            "forecast": forecast,
            "reward": reward,
        }
        self._entries.append(entry)
        return entry

    def log_action_execution(self, action: Dict[str, Any], status: str, error: Optional[str] = None) -> Dict[str, Any]:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "execution",
            "action": action,
            "status": status,
            "error": error,
        }
        self._entries.append(entry)
        return entry

    def get_audit_trail(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if not filters:
            return list(self._entries)

        def _matches(entry: Dict[str, Any]) -> bool:
            return all(entry.get(key) == value for key, value in filters.items())

        return [entry for entry in self._entries if _matches(entry)]
