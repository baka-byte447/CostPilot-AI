from .vmss_controller import VMSSController
from .aci_controller import ACIController
from .cost_controller import AzureCostController

_vmss_ctrl = None
_aci_ctrl = None
_azure_cost = None

def get_vmss_ctrl():
    global _vmss_ctrl
    if _vmss_ctrl is None:
        _vmss_ctrl = VMSSController()
    return _vmss_ctrl

def get_aci_ctrl():
    global _aci_ctrl
    if _aci_ctrl is None:
        _aci_ctrl = ACIController()
    return _aci_ctrl

def get_azure_cost():
    global _azure_cost
    if _azure_cost is None:
        _azure_cost = AzureCostController()
    return _azure_cost

vmss_ctrl = get_vmss_ctrl
aci_ctrl = get_aci_ctrl
azure_cost = get_azure_cost