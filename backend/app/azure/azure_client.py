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

    def __init__(self, creds: dict = None):
        if creds:
            self.subscription_id  = creds.get("subscription_id")
            self.resource_group   = creds.get("resource_group", "nimbusopt-rg")
            self.location         = creds.get("location", "eastus")
            self.credential = ClientSecretCredential(
                tenant_id     = creds.get("tenant_id", ""),
                client_id     = creds.get("client_id", ""),
                client_secret = creds.get("client_secret", "")
            )
        else:
            self.subscription_id  = os.getenv("AZURE_SUBSCRIPTION_ID")
            self.resource_group   = os.getenv("AZURE_RESOURCE_GROUP", "nimbusopt-rg")
            self.location         = os.getenv("AZURE_LOCATION", "eastus")
            self.credential = ClientSecretCredential(
                tenant_id     = os.getenv("AZURE_TENANT_ID", ""),
                client_id     = os.getenv("AZURE_CLIENT_ID", ""),
                client_secret = os.getenv("AZURE_CLIENT_SECRET", "")
            )

    def compute(self) -> ComputeManagementClient:
        return ComputeManagementClient(self.credential, self.subscription_id)

    def container(self) -> ContainerInstanceManagementClient:
        return ContainerInstanceManagementClient(self.credential, self.subscription_id)

    def monitor(self) -> MonitorManagementClient:
        return MonitorManagementClient(self.credential, self.subscription_id)

    def cost(self) -> CostManagementClient:
        return CostManagementClient(self.credential)

    def resource(self) -> ResourceManagementClient:
        return ResourceManagementClient(self.credential, self.subscription_id)
