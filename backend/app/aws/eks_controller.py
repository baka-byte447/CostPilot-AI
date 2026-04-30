import logging

from .aws_client import get_default_aws_manager

logger = logging.getLogger(__name__)
class EKSController:
    def __init__(self, aws_manager=None):
        self.aws = aws_manager or get_default_aws_manager()

    def get_nodegroup_info(self, cluster: str, nodegroup: str) -> dict:
        resp = self.aws.eks().describe_nodegroup(
            clusterName=cluster,
            nodegroupName=nodegroup
        )
        ng = resp["nodegroup"]
        sc = ng["scalingConfig"]
        return {
            "cluster": cluster,
            "nodegroup": nodegroup,
            "desired": sc["desiredSize"],
            "min": sc["minSize"],
            "max": sc["maxSize"],
            "status": ng["status"],
            "instance_types": ng.get("instanceTypes", []),
        }

    def set_desired_size(self, cluster: str, nodegroup: str, desired: int) -> dict:
        info = self.get_nodegroup_info(cluster, nodegroup)
        desired = max(info["min"], min(info["max"], desired))

        if desired == info["desired"]:
            return {"action": "no_change", "desired": desired}

        self.aws.eks().update_nodegroup_config(
            clusterName=cluster,
            nodegroupName=nodegroup,
            scalingConfig={"desiredSize": desired}
        )
        direction = "scale_up" if desired > info["desired"] else "scale_down"
        logger.info(f"EKS {cluster}/{nodegroup}: {direction} {info['desired']}→{desired}")
        return {
            "action": direction,
            "cluster": cluster,
            "nodegroup": nodegroup,
            "previous": info["desired"],
            "desired": desired
        }

    def scale_up(self, cluster: str, nodegroup: str, increment: int = 1) -> dict:
        info = self.get_nodegroup_info(cluster, nodegroup)
        return self.set_desired_size(cluster, nodegroup, info["desired"] + increment)

    def scale_down(self, cluster: str, nodegroup: str, decrement: int = 1) -> dict:
        info = self.get_nodegroup_info(cluster, nodegroup)
        return self.set_desired_size(cluster, nodegroup, info["desired"] - decrement)

    def list_nodegroups(self, cluster: str) -> list:
        resp = self.aws.eks().list_nodegroups(clusterName=cluster)
        nodegroups = []
        for ng_name in resp.get("nodegroups", []):
            try:
                nodegroups.append(self.get_nodegroup_info(cluster, ng_name))
            except Exception as e:
                logger.warning(f"Could not describe nodegroup {ng_name}: {e}")
        return nodegroups

    def list_clusters(self) -> list:
        resp = self.aws.eks().list_clusters()
        return resp.get("clusters", [])
    

    