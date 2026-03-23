from .vmss_controller import VMSSController
from .aci_controller import ACIController
from .cost_controller import AzureCostController

vmss_ctrl = VMSSController()
aci_ctrl  = ACIController()
azure_cost = AzureCostController()

