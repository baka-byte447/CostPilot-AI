"""Orchestration executor stub with structured responses."""

import logging
from typing import Any, Dict, Optional


logger = logging.getLogger(__name__)


class InfrastructureExecutor:
    """Executes scaling actions on cloud infrastructure."""

    def __init__(self, cloud_provider: str = "aws"):
        self.cloud_provider = cloud_provider
        self._last_result: Optional[Dict[str, Any]] = None

    def _record(self, action: str, service_name: str, count: int, status: str = "success", details: Optional[str] = None) -> Dict[str, Any]:
        self._last_result = {
            "action": action,
            "service": service_name,
            "count": count,
            "status": status,
            "details": details,
            "provider": self.cloud_provider,
        }
        logger.info("%s on %s -> %s", action, service_name, status)
        return self._last_result

    def scale_up_instances(self, service_name: str, count: int) -> Dict[str, Any]:
        return self._record("scale_up", service_name, count)

    def scale_down_instances(self, service_name: str, count: int) -> Dict[str, Any]:
        return self._record("scale_down", service_name, count)

    def deploy_update(self, service_name: str, new_config: Dict[str, Any]) -> Dict[str, Any]:
        details = f"applied config keys: {', '.join(new_config.keys())}" if new_config else "no changes"
        return self._record("deploy_update", service_name, 0, details=details)

    def get_executable_status(self) -> Optional[Dict[str, Any]]:
        return self._last_result
