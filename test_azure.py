import sys
import os
sys.path.insert(0, "backend")

os.environ.setdefault("AZURE_CLIENT_ID",       "f547823c-6d41-4116-994c-00d0d3b22b0f")
os.environ.setdefault("AZURE_CLIENT_SECRET",   "Ytn8Q~Sywi_8Qhb21kCUhdX9jNxTGf1oPElWharK")
os.environ.setdefault("AZURE_SUBSCRIPTION_ID", "c7a98a3a-c5b6-4c33-b3c2-96bd4a6684e7")
os.environ.setdefault("AZURE_TENANT_ID",       "2770f6e2-f99f-481e-b493-41937886efb0")
os.environ.setdefault("AZURE_RESOURCE_GROUP",  "nimbusopt-rg")
os.environ.setdefault("AZURE_LOCATION",        "centralindia")
os.environ.setdefault("AZURE_VMSS_NAME",       "nimbusopt-vmss")
os.environ.setdefault("AZURE_ACI_GROUP",       "nimbusopt-containers")

from app.azure.azure_client import azure


try:
    rg = azure.resource().resource_groups.get("nimbusopt-rg")
    print(f"Azure credentials valid — resource group: {rg.name} ({rg.location})")
except Exception as e:
    print(f"Credential check failed: {e}")
    exit(1)
try:
    from app.azure.vmss_controller import VMSSController
    ctrl = VMSSController()
    vmss_list = ctrl.list_vmss()
    print(f" VMSS access OK — found {len(vmss_list)} scale set(s)")
    for v in vmss_list:
        print(f"  - {v['name']} (capacity={v['capacity']}, size={v['vm_size']})")
except Exception as e:
    print(f"VMSS access failed: {e}")
try:
    from app.azure.aci_controller import ACIController
    ctrl = ACIController()
    groups = ctrl.list_groups()
    print(f" ACI access OK — found {len(groups)} container group(s)")
    for g in groups:
        print(f"  - {g['name']} ({g['state']})")
except Exception as e:
    print(f"ACI access failed: {e}")

try:
    from app.azure.cost_controller import AzureCostController
    ctrl = AzureCostController()
    cost = ctrl.get_current_month_cost()
    print(f" Cost API OK — MTD spend: ${cost['amount']}")
except Exception as e:
    print(f"Cost API failed: {e}")