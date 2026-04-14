import logging
from .aws_client import aws

logger = logging.getLogger(__name__)
class ECSController:

    def get_service_info(self, cluster: str, service: str) -> dict:
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
        info = self.get_service_info(cluster, service)
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
        resp = aws.ecs().list_clusters()
        return resp.get("clusterArns", [])
    
    