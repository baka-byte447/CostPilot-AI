import logging
import os
from .azure_client import AzureClientManager
from azure.mgmt.containerinstance.models import OperatingSystemTypes

logger=logging.getLogger(__name__)


class ACIController:

    def __init__(self, creds: dict = None):
        self.azure = AzureClientManager(creds)
        self.resource_group=self.azure.resource_group
        self.location = creds.get("location", "centralindia") if creds else os.getenv("AZURE_LOCATION","centralindia")
        self.base_name=os.getenv("AZURE_ACI_GROUP", "nimbusopt-containers")

    MAX_ACI_GROUPS =2

    def _get_all_groups(self)->list:
        container=self.azure.container()
        all_groups=list(
            container.container_groups.list_by_resource_group(self.resource_group)
        )
        return[g for g in all_groups if g.name.startswith(self.base_name)]

    def get_info(self)->dict:

        groups=self._get_all_groups()

        return{
            "base_name": self.base_name,
            "running_groups":len(groups),
            "groups":[
                {
                    "name": g.name,
                    "state":g.instance_view.state if g.instance_view else "Unknown",
                    "ip":g.ip_address.ip if g.ip_address else None,
                }
                for g in groups
            ],
        }

    def scale_up(self,increment:int=1,image:str="nginx:latest", cpu:float=0.5,memory:float=0.5)->dict:

        existing = self._get_all_groups()

        if len(existing)>=MAX_ACI_GROUPS:
            return{
                "action":"no_change",
                "reason": f"at max capacity ({MAX_ACI_GROUPS} groups)",
                "total_groups": len(existing),
            }

            container_client=self.azure.container()
            existing=self._get_all_groups()
            created=[]

            for i in range(increment):

                new_index=len(existing)+i+1
                group_name=f"{self.base_name}-{new_index}"

                container_group=ContainerGroup(
                    location=self.location,
                    containers=[
                        Container(
                            name="app",
                            image=image,
                            resources=ResourceRequirements(
                                requests=ResourceRequests(cpu=cpu,memory_in_gb=memory)
                            ),
                            ports=[ContainerPort(port=80)],
                        )
                    ],
                    os_type=OperatingSystemTypes.LINUX,
                    ip_address=IpAddress(
                        ports=[Port(protocol="TCP",port=80)],type="Public"
                    ),
                )

                poller = container_client.container_groups.begin_create_or_update(
                    self.resource_group,group_name,container_group
                )

                poller.result()

                created.append(group_name)
                logger.info(f"ACI: created container group {group_name}")

            return{
                "action":"scale_up",
                "created": created,
                "total_groups":len(existing)+increment,
            }

    def scale_down(self,decrement:int=1)->dict:

        container_client = self.azure.container()

        groups=sorted(self._get_all_groups(),key=lambda g: g.name,reverse=True)

        if len(groups)<=1:
            return {"action":"no_change","reason":"already at minimum (1 group)"}

        to_delete=groups[:min(decrement,len(groups)-1)]

        deleted = []

        for group in to_delete:

            poller=container_client.container_groups.begin_delete(
                self.resource_group, group.name
            )

            poller.result()
            deleted.append(group.name)

            logger.info(f"ACI: deleted container group {group.name}")

        return{
            "action":"scale_down",
            "deleted":deleted,
            "total_groups": len(groups)-len(deleted),
        }

    def list_groups(self)->list:

        return[
            {
                "name":g.name,
                "state": g.instance_view.state if g.instance_view else "Unknown",
                "location": g.location,
                "ip":g.ip_address.ip if g.ip_address else None,
            }
            for g in self._get_all_groups()
        ]
    

