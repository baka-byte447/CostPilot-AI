
import time
from datetime import datetime, timezone

_state = {
    "asgs": {
        "nimbusopt-asg": {
            "name": "nimbusopt-asg",
            "desired": 2,
            "min": 1,
            "max": 6,
            "instances": 2,
            "healthy": 2,
        }
    },
    "ecs_clusters": {
        "nimbusopt-cluster": {
            "services": {
                "nimbusopt-service": {
                    "desired": 2,
                    "running": 2,
                    "pending": 0,
                    "status": "ACTIVE"
                }
            }
        }
    },
    "eks_clusters": {
        "nimbusopt-eks": {
            "nodegroups": {
                "nimbusopt-nodegroup": {
                    "desired": 2,
                    "min": 1,
                    "max": 5,
                    "status": "ACTIVE",
                    "instance_types": ["t3.medium"]
                }
            }
        }
    },
    "actions_log": []
}
class MockEC2Controller:

    def get_asg_info(self, asg_name: str) -> dict:
        if asg_name not in _state["asgs"]:
            raise ValueError(f"ASG '{asg_name}' not found")
        return _state["asgs"][asg_name].copy()

    def set_desired_capacity(self, asg_name: str, desired: int) -> dict:
        if asg_name not in _state["asgs"]:
            raise ValueError(f"ASG '{asg_name}' not found")
        asg = _state["asgs"][asg_name]
        desired = max(asg["min"], min(asg["max"], desired))
        if desired == asg["desired"]:
            return {"action": "no_change", "desired": desired}
        direction = "scale_up" if desired > asg["desired"] else "scale_down"
        prev = asg["desired"]
        asg["desired"] = desired
        asg["instances"] = desired
        asg["healthy"] = desired
        _log_action("ec2", direction, asg_name, prev, desired)
        return {"action": direction, "previous": prev, "desired": desired, "asg": asg_name}

    def scale_up(self, asg_name: str, increment: int = 1) -> dict:
        info = self.get_asg_info(asg_name)
        return self.set_desired_capacity(asg_name, info["desired"] + increment)

    def scale_down(self, asg_name: str, decrement: int = 1) -> dict:
        info = self.get_asg_info(asg_name)
        return self.set_desired_capacity(asg_name, info["desired"] - decrement)

    def terminate_idle_instances(self, asg_name: str,
                                  cpu_threshold: float = 5.0) -> dict:
        info = self.get_asg_info(asg_name)
        if info["instances"] > info["min"]:
            self.scale_down(asg_name, 1)
            return {"action": "terminate_idle", "asg": asg_name,
                    "terminated": ["i-mock001"], "count": 1}
        return {"action": "terminate_idle", "asg": asg_name,
                "terminated": [], "count": 0}

    def change_instance_type(self, instance_id: str, new_type: str) -> dict:
        _log_action("ec2", "change_instance_type", instance_id, None, new_type)
        return {"action": "change_instance_type",
                "instance_id": instance_id, "new_type": new_type}

    def list_asgs(self) -> list:
        return list(_state["asgs"].values())



class MockECSController:

    def get_service_info(self, cluster: str, service: str) -> dict:
        if cluster not in _state["ecs_clusters"]:
            raise ValueError(f"Cluster '{cluster}' not found")
        services = _state["ecs_clusters"][cluster]["services"]
        if service not in services:
            raise ValueError(f"Service '{service}' not found in '{cluster}'")
        s = services[service]
        return {"service": service, "cluster": cluster, **s}

    def set_desired_count(self, cluster: str, service: str, desired: int) -> dict:
        desired = max(1, desired)
        info = self.get_service_info(cluster, service)
        if desired == info["desired"]:
            return {"action": "no_change", "desired": desired}
        direction = "scale_up" if desired > info["desired"] else "scale_down"
        prev = info["desired"]
        _state["ecs_clusters"][cluster]["services"][service]["desired"] = desired
        _state["ecs_clusters"][cluster]["services"][service]["running"] = desired
        _log_action("ecs", direction, f"{cluster}/{service}", prev, desired)
        return {"action": direction, "cluster": cluster, "service": service,
                "previous": prev, "desired": desired}

    def scale_up(self, cluster: str, service: str, increment: int = 1) -> dict:
        info = self.get_service_info(cluster, service)
        return self.set_desired_count(cluster, service, info["desired"] + increment)

    def scale_down(self, cluster: str, service: str, decrement: int = 1) -> dict:
        info = self.get_service_info(cluster, service)
        return self.set_desired_count(cluster, service, info["desired"] - decrement)

    def list_services(self, cluster: str) -> list:
        if cluster not in _state["ecs_clusters"]:
            return []
        return [
            {"service": k, **v}
            for k, v in _state["ecs_clusters"][cluster]["services"].items()
        ]

    def list_clusters(self) -> list:
        return list(_state["ecs_clusters"].keys())
class MockEKSController:

    def get_nodegroup_info(self, cluster: str, nodegroup: str) -> dict:
        if cluster not in _state["eks_clusters"]:
            raise ValueError(f"EKS cluster '{cluster}' not found")
        ngs = _state["eks_clusters"][cluster]["nodegroups"]
        if nodegroup not in ngs:
            raise ValueError(f"Nodegroup '{nodegroup}' not found")
        ng = ngs[nodegroup]
        return {"cluster": cluster, "nodegroup": nodegroup, **ng}

    def set_desired_size(self, cluster: str, nodegroup: str, desired: int) -> dict:
        info = self.get_nodegroup_info(cluster, nodegroup)
        desired = max(info["min"], min(info["max"], desired))
        if desired == info["desired"]:
            return {"action": "no_change", "desired": desired}
        direction = "scale_up" if desired > info["desired"] else "scale_down"
        prev = info["desired"]
        _state["eks_clusters"][cluster]["nodegroups"][nodegroup]["desired"] = desired
        _log_action("eks", direction, f"{cluster}/{nodegroup}", prev, desired)
        return {"action": direction, "cluster": cluster, "nodegroup": nodegroup,
                "previous": prev, "desired": desired}

    def scale_up(self, cluster: str, nodegroup: str, increment: int = 1) -> dict:
        info = self.get_nodegroup_info(cluster, nodegroup)
        return self.set_desired_size(cluster, nodegroup, info["desired"] + increment)

    def scale_down(self, cluster: str, nodegroup: str, decrement: int = 1) -> dict:
        info = self.get_nodegroup_info(cluster, nodegroup)
        return self.set_desired_size(cluster, nodegroup, info["desired"] - decrement)

    def list_nodegroups(self, cluster: str) -> list:
        if cluster not in _state["eks_clusters"]:
            return []
        return [
            {"cluster": cluster, "nodegroup": k, **v}
            for k, v in _state["eks_clusters"][cluster]["nodegroups"].items()
        ]

    def list_clusters(self) -> list:
        return list(_state["eks_clusters"].keys())
class MockCostExplorer:

    def get_current_month_cost(self) -> dict:
        total = sum(
            a["desired"] * 0.0416
            for a in _state["asgs"].values()
        )
        return {
            "amount": round(total * 24 * 28, 2),
            "currency": "USD",
            "period_start": "2026-03-01",
            "period_end": datetime.now(timezone.utc).strftime("%Y-%m-%d")
        }

    def get_daily_cost(self, days: int = 7) -> list:
        from datetime import timedelta
        today = datetime.now(timezone.utc).date()
        return [
            {
                "date": str(today - timedelta(days=i)),
                "total": round(sum(
                    a["desired"] * 0.0416 * 24
                    for a in _state["asgs"].values()
                ), 4),
                "by_service": {"Amazon EC2": 0.8, "Amazon ECS": 0.2}
            }
            for i in range(days - 1, -1, -1)
        ]

    def get_cost_forecast(self, days_ahead: int = 30) -> dict:
        daily = sum(a["desired"] * 0.0416 * 24 for a in _state["asgs"].values())
        return {
            "forecast_amount": round(daily * days_ahead, 2),
            "currency": "USD",
            "forecast_days": days_ahead
        }

def _log_action(resource_type, action, target, previous, new):
    _state["actions_log"].append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "resource_type": resource_type,
        "action": action,
        "target": target,
        "previous": previous,
        "new": new
    })
    # Keeplast 50
    if len(_state["actions_log"]) > 50:
        _state["actions_log"].pop(0)

def get_actions_log() -> list:
    return list(reversed(_state["actions_log"]))