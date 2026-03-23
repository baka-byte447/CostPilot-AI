import logging
import os
from .azure_client import azure
from azure.mgmt.containerinstance.models import OperatingSystemTypes
logger = logging.getLogger(__name__)


class ACIController:
    """
    Controls Azure Container Instances.
    ACI is serverless containers — you scale by adding/removing
    container groups. Each group is like one ECS task.

    Scaling model:
      scale_up   → create a new container group (nimbusopt-containers-N)
      scale_down → delete the highest-numbered container group
      list       → show all running container groups with this prefix
    """

    def __init__(self):
        self.resource_group = os.getenv("AZURE_RESOURCE_GROUP", "nimbusopt-rg")
        self.location       = os.getenv("AZURE_LOCATION", "centralindia")
        self.base_name      = os.getenv("AZURE_ACI_GROUP", "nimbusopt-containers")

    def _get_all_groups(self) -> list:
        """Returns all container groups matching our base name prefix."""
        container = azure.container()
        all_groups = list(container.container_groups.list_by_resource_group(
            self.resource_group
        ))
        return [g for g in all_groups if g.name.startswith(self.base_name)]

    def get_info(self) -> dict:
        """Returns current state of all managed container groups."""
        groups = self._get_all_groups()
        return {
            "base_name": self.base_name,
            "running_groups": len(groups),
            "groups": [
                {
                    "name": g.name,
                    "state": g.instance_view.state if g.instance_view else "Unknown",
                    "ip": g.ip_address.ip if g.ip_address else None
                }
                for g in groups
            ]
        }

    def scale_up(self, increment: int = 1,
                 image: str = "nginx:latest",
                 cpu: float = 0.5,
                 memory: float = 0.5) -> dict:
        """
        Creates `increment` new container groups.
        Each group runs one container — cheap at ~$0.000003/second.
        """
        from azure.mgmt.containerinstance.models import (
            ContainerGroup, Container, ContainerPort,
            ResourceRequirements, ResourceRequests,
            OperatingSystemTypes, IpAddress, Port
        )

        container_client = azure.container()
        existing = self._get_all_groups()
        created = []

        for i in range(increment):
            # Name like: nimbusopt-containers-3
            new_index = len(existing) + i + 1
            group_name = f"{self.base_name}-{new_index}"

            container_group = ContainerGroup(
                location=self.location,
                containers=[
                    Container(
                        name="app",
                        image=image,
                        resources=ResourceRequirements(
                            requests=ResourceRequests(cpu=cpu, memory_in_gb=memory)
                        ),
                        ports=[ContainerPort(port=80)]
                    )
                ],
                os_type=OperatingSystemTypes.LINUX,
                ip_address=IpAddress(
                    ports=[Port(protocol="TCP", port=80)],
                    type="Public"
                )
            )

            poller = container_client.container_groups.begin_create_or_update(
                self.resource_group, group_name, container_group
            )
            poller.result()
            created.append(group_name)
            logger.info(f"ACI: created container group {group_name}")

        return {
            "action": "scale_up",
            "created": created,
            "total_groups": len(existing) + increment
        }

    def scale_down(self, decrement: int = 1) -> dict:
        """
        Deletes the highest-numbered container groups.
        Protects against deleting below 1 running group.
        """
        container_client = azure.container()
        groups = sorted(self._get_all_groups(), key=lambda g: g.name, reverse=True)

        if len(groups) <= 1:
            return {"action": "no_change", "reason": "already at minimum (1 group)"}

        # Only delete up to (total - 1) so we always keep at least one running
        to_delete = groups[:min(decrement, len(groups) - 1)]
        deleted = []

        for group in to_delete:
            poller = container_client.container_groups.begin_delete(
                self.resource_group, group.name
            )
            poller.result()
            deleted.append(group.name)
            logger.info(f"ACI: deleted container group {group.name}")

        return {
            "action": "scale_down",
            "deleted": deleted,
            "total_groups": len(groups) - len(deleted)
        }

    def list_groups(self) -> list:
        """List all managed container groups."""
        return [
            {
                "name": g.name,
                "state": g.instance_view.state if g.instance_view else "Unknown",
                "location": g.location,
                "ip": g.ip_address.ip if g.ip_address else None
            }
            for g in self._get_all_groups()
        ]