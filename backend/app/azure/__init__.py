import os
from typing import Optional

from azure.identity import ClientSecretCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.containerinstance import ContainerInstanceManagementClient
from azure.mgmt.costmanagement import CostManagementClient
from azure.mgmt.resource import ResourceManagementClient

from .vmss_controller import VMSSController
from .aci_controller import ACIController
from .cost_controller import AzureCostController

_vmss_ctrl = None
_aci_ctrl = None
_azure_cost = None


def _make_azure_credential(creds: Optional[dict] = None) -> ClientSecretCredential:
    if creds:
        return ClientSecretCredential(
            tenant_id=creds["tenant_id"],
            client_id=creds["client_id"],
            client_secret=creds["client_secret"],
        )
    return ClientSecretCredential(
        tenant_id=os.getenv("AZURE_TENANT_ID", ""),
        client_id=os.getenv("AZURE_CLIENT_ID", ""),
        client_secret=os.getenv("AZURE_CLIENT_SECRET", ""),
    )


def get_vmss_ctrl(creds: Optional[dict] = None) -> VMSSController:
    global _vmss_ctrl
    if creds:
        return VMSSController()
    if _vmss_ctrl is None:
        _vmss_ctrl = VMSSController()
    return _vmss_ctrl


def get_aci_ctrl(creds: Optional[dict] = None) -> ACIController:
    global _aci_ctrl
    if creds:
        return ACIController()
    if _aci_ctrl is None:
        _aci_ctrl = ACIController()
    return _aci_ctrl


def get_azure_cost(creds: Optional[dict] = None) -> AzureCostController:
    global _azure_cost
    if creds:
        return AzureCostController()
    if _azure_cost is None:
        _azure_cost = AzureCostController()
    return _azure_cost


vmss_ctrl = get_vmss_ctrl
aci_ctrl = get_aci_ctrl
azure_cost = get_azure_cost