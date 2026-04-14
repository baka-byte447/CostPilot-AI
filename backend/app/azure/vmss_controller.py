import logging
import os
from .azure_client import azure

logger=logging.getLogger(__name__)


class VMSSController:

    def __init__(self):
        self.resource_group = os.getenv("AZURE_RESOURCE_GROUP","nimbusopt-rg")

    def get_vmss_info(self,vmss_name:str)->dict:

        compute = azure.compute()

        vmss=compute.virtual_machine_scale_sets.get(
            self.resource_group,vmss_name
        )

        instances=list(
            compute.virtual_machine_scale_set_vms.list(
                self.resource_group, vmss_name
            )
        )

        capacity = vmss.sku.capacity

        return{
            "name":vmss_name,
            "capacity": capacity,
            "instance_count":len(instances),
            "vm_size": vmss.sku.name,
            "location":vmss.location,
            "provisioning_state": vmss.provisioning_state
        }

    def set_capacity(self,vmss_name:str,capacity:int)->dict:

        capacity=max(1,capacity)

        info = self.get_vmss_info(vmss_name)

        if capacity == info["capacity"]:
            return {"action":"no_change","capacity":capacity}

        compute=azure.compute()

        vmss = compute.virtual_machine_scale_sets.get(
            self.resource_group,
            vmss_name
        )

        vmss.sku.capacity=capacity

        poller=compute.virtual_machine_scale_sets.begin_create_or_update(
            self.resource_group,
            vmss_name,
            vmss
        )

        poller.result()

        direction="scale_up" if capacity>info["capacity"] else "scale_down"

        logger.info(f"VMSS {vmss_name}: {direction} {info['capacity']}→{capacity}")

        return{
            "action":direction,
            "vmss":vmss_name,
            "previous": info["capacity"],
            "capacity":capacity
        }

    def scale_up(self,vmss_name:str,increment:int=1)->dict:

        info=self.get_vmss_info(vmss_name)

        return self.set_capacity(vmss_name, info["capacity"]+increment)

    def scale_down(self, vmss_name:str,decrement:int=1)->dict:

        info = self.get_vmss_info(vmss_name)

        return self.set_capacity(vmss_name,info["capacity"]-decrement)

    def terminate_idle_instances(self,vmss_name:str,cpu_threshold:float=5.0)->dict:

        from datetime import datetime,timezone,timedelta

        compute=azure.compute()
        monitor = azure.monitor()

        instances=list(
            compute.virtual_machine_scale_set_vms.list(
                self.resource_group,vmss_name
            )
        )

        idle_instance_ids=[]

        for inst in instances:

            resource_id=inst.id
            now = datetime.now(timezone.utc)

            try:
                metrics = monitor.metrics.list(
                    resource_id,
                    timespan=f"{(now - timedelta(minutes=10)).isoformat()}/{now.isoformat()}",
                    interval="PT5M",
                    metricnames="Percentage CPU",
                    aggregation="Average"
                )

                for metric in metrics.value:
                    for ts in metric.timeseries:
                        for dp in ts.data:

                            if dp.average is not None and dp.average < cpu_threshold:
                                idle_instance_ids.append(inst.instance_id)

            except Exception as e:
                logger.warning(f"Could not get metrics for instance {inst.instance_id}: {e}")

        if idle_instance_ids:

            from azure.mgmt.compute.models import VirtualMachineScaleSetVMInstanceIDs

            poller = compute.virtual_machine_scale_sets.begin_delete_instances(
                self.resource_group,
                vmss_name,
                VirtualMachineScaleSetVMInstanceIDs(instance_ids=idle_instance_ids)
            )

            poller.result()

            logger.info(f"VMSS {vmss_name}: terminated {len(idle_instance_ids)} idle instances")

        return{
            "action":"terminate_idle",
            "vmss":vmss_name,
            "checked":len(instances),
            "terminated":idle_instance_ids,
            "count": len(idle_instance_ids)
        }

    def change_vm_size(self,vmss_name:str,new_size:str)->dict:

        compute = azure.compute()

        vmss=compute.virtual_machine_scale_sets.get(
            self.resource_group, vmss_name
        )

        old_size=vmss.sku.name
        vmss.sku.name=new_size

        poller=compute.virtual_machine_scale_sets.begin_create_or_update(
            self.resource_group,vmss_name,vmss
        )

        poller.result()

        logger.info(f"VMSS {vmss_name}: size changed {old_size}→{new_size}")

        return{
            "action":"change_vm_size",
            "vmss":vmss_name,
            "old_size":old_size,
            "new_size": new_size
        }

    def list_vmss(self)->list:

        compute=azure.compute()

        return[
            {
                "name": v.name,
                "capacity":v.sku.capacity,
                "vm_size": v.sku.name,
                "location":v.location,
                "state": v.provisioning_state
            }
            for v in compute.virtual_machine_scale_sets.list(self.resource_group)
        ]