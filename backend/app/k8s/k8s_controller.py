import logging
from typing import Any, Dict

from kubernetes import client, config
from kubernetes.config.config_exception import ConfigException

from app.config.settings import settings


logger = logging.getLogger(__name__)


def _load_kube_config() -> None:
    """Load kubeconfig from a provided path or fall back to defaults."""
    try:
        if settings.kube_config_path:
            config.load_kube_config(settings.kube_config_path)
        else:
            config.load_kube_config()
    except ConfigException:
        # Allow running inside a cluster if config file is absent
        try:
            config.load_incluster_config()
        except Exception as exc:  # pragma: no cover - environment specific
            logger.error("Failed to load Kubernetes configuration: %s", exc)
            raise


def scale_deployment(deployment_name: str, namespace: str, replicas: int) -> Dict[str, Any]:
    """Scale a Kubernetes deployment to the desired replica count."""
    _load_kube_config()

    api = client.AppsV1Api()
    body = {"spec": {"replicas": replicas}}

    api.patch_namespaced_deployment_scale(
        name=deployment_name,
        namespace=namespace,
        body=body,
    )

    return {"deployment": deployment_name, "new_replicas": replicas}