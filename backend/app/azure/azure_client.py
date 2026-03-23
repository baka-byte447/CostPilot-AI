import os
from dotenv import load_dotenv
from azure.identity import ClientSecretCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.containerinstance import ContainerInstanceManagementClient
from azure.mgmt.monitor import MonitorManagementClient
from azure.mgmt.costmanagement import CostManagementClient
from azure.mgmt.resource import ResourceManagementClient

load_dotenv()


class AzureClientManager:
    """
    Central Azure SDK client manager.
    Uses a Service Principal (clientId + clientSecret) for auth.
    All controllers import from this singleton.
    """

    def __init__(self):
        self.subscription_id  = os.getenv("AZURE_SUBSCRIPTION_ID")
        self.resource_group   = os.getenv("AZURE_RESOURCE_GROUP", "nimbusopt-rg")
        self.location         = os.getenv("AZURE_LOCATION", "eastus")

        # ClientSecretCredential = Service Principal auth
        self.credential = ClientSecretCredential(
            tenant_id     = os.getenv("AZURE_TENANT_ID"),
            client_id     = os.getenv("AZURE_CLIENT_ID"),
            client_secret = os.getenv("AZURE_CLIENT_SECRET")
        )

    def compute(self) -> ComputeManagementClient:
        """Covers VMs, VMSS, disks."""
        return ComputeManagementClient(self.credential, self.subscription_id)

    def container(self) -> ContainerInstanceManagementClient:
        """Covers Azure Container Instances (ACI)."""
        return ContainerInstanceManagementClient(self.credential, self.subscription_id)

    def monitor(self) -> MonitorManagementClient:
        """Covers Azure Monitor metrics (CPU, memory)."""
        return MonitorManagementClient(self.credential, self.subscription_id)

    def cost(self) -> CostManagementClient:
        """Covers Azure Cost Management API."""
        return CostManagementClient(self.credential)

    def resource(self) -> ResourceManagementClient:
        """Covers resource groups and general resource operations."""
        return ResourceManagementClient(self.credential, self.subscription_id)


# Singleton — import this everywhere
azure = AzureClientManager()