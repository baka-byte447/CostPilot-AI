import logging
from .aws_client import aws

logger = logging.getLogger(__name__)


class EKSController:
    """
    Controls EKS managed node groups.
    Node groups are the AWS equivalent of your local Docker Desktop
    Kubernetes nodes — except they're real EC2s managed by EKS.
    """

    def get_nodegroup_info(self, cluster: str, nodegroup: str) -> dict:
        """Returns current scaling config of an EKS node group."""
        resp = aws.eks().describe_nodegroup(
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
        """
        Scale a node group to a specific size.
        EKS will add or remove EC2 nodes and reschedule pods automatically.
        """
        info = self.get_nodegroup_info(cluster, nodegroup)
        desired = max(info["min"], min(info["max"], desired))

        if desired == info["desired"]:
            return {"action": "no_change", "desired": desired}

        aws.eks().update_nodegroup_config(
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
        """List all node groups in an EKS cluster."""
        resp = aws.eks().list_nodegroups(clusterName=cluster)
        nodegroups = []
        for ng_name in resp.get("nodegroups", []):
            try:
                nodegroups.append(self.get_nodegroup_info(cluster, ng_name))
            except Exception as e:
                logger.warning(f"Could not describe nodegroup {ng_name}: {e}")
        return nodegroups

    def list_clusters(self) -> list:
        resp = aws.eks().list_clusters()
        return resp.get("clusters", [])
    

    