import logging
from .aws_client import aws

logger = logging.getLogger(__name__)


class ECSController:
    """
    Controls ECS service scaling on behalf of the RL agent.
    Each ECS 'service' is like a deployment — it has a desired
    task count that we increase or decrease.
    """

    def get_service_info(self, cluster: str, service: str) -> dict:
        """Returns current state of an ECS service."""
        resp = aws.ecs().describe_services(
            cluster=cluster,
            services=[service]
        )
        services = resp.get("services", [])
        if not services:
            raise ValueError(f"ECS service '{service}' not found in cluster '{cluster}'")
        s = services[0]
        return {
            "service": s["serviceName"],
            "cluster": cluster,
            "desired": s["desiredCount"],
            "running": s["runningCount"],
            "pending": s["pendingCount"],
            "status": s["status"],
        }

    def set_desired_count(self, cluster: str, service: str, desired: int) -> dict:
        """
        Core action: update the desired task count of an ECS service.
        ECS will launch or drain tasks to reach this count.
        """
        info = self.get_service_info(cluster, service)

        # Protect against scaling to zero accidentally
        desired = max(1, desired)

        if desired == info["desired"]:
            return {"action": "no_change", "desired": desired}

        aws.ecs().update_service(
            cluster=cluster,
            service=service,
            desiredCount=desired
        )
        direction = "scale_up" if desired > info["desired"] else "scale_down"
        logger.info(f"ECS {cluster}/{service}: {direction} {info['desired']}→{desired}")
        return {
            "action": direction,
            "cluster": cluster,
            "service": service,
            "previous": info["desired"],
            "desired": desired
        }

    def scale_up(self, cluster: str, service: str, increment: int = 1) -> dict:
        info = self.get_service_info(cluster, service)
        return self.set_desired_count(cluster, service, info["desired"] + increment)

    def scale_down(self, cluster: str, service: str, decrement: int = 1) -> dict:
        info = self.get_service_info(cluster, service)
        return self.set_desired_count(cluster, service, info["desired"] - decrement)

    def list_services(self, cluster: str) -> list:
        """List all services in an ECS cluster with their current counts."""
        resp = aws.ecs().list_services(cluster=cluster)
        arns = resp.get("serviceArns", [])
        if not arns:
            return []
        details = aws.ecs().describe_services(cluster=cluster, services=arns)
        return [
            {
                "service": s["serviceName"],
                "desired": s["desiredCount"],
                "running": s["runningCount"],
                "status": s["status"]
            }
            for s in details.get("services", [])
        ]

    def list_clusters(self) -> list:
        """List all ECS cluster names in the region."""
        resp = aws.ecs().list_clusters()
        return resp.get("clusterArns", [])