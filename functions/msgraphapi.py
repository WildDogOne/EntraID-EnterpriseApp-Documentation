from msgraph import GraphServiceClient
from kestra import Kestra

logger = Kestra.logger()

from kiota_abstractions.base_request_configuration import RequestConfiguration
from azure.identity.aio import ClientSecretCredential


class GraphAPI:
    def __init__(
        self, azure_tenant_id=None, azure_client_id=None, azure_client_secret=None
    ):
        self.azure_tenant_id = azure_tenant_id
        self.azure_client_id = azure_client_id
        self.azure_client_secret = azure_client_secret
        self._auth()

    def _auth(self):
        self.credential = ClientSecretCredential(
            self.azure_tenant_id, self.azure_client_id, self.azure_client_secret
        )
        self.scopes = ["https://graph.microsoft.com/.default"]
        self.graph_client = GraphServiceClient(self.credential, scopes=self.scopes)

    async def get_all_enterprise_apps(self):
        users = []
        logger.debug("Getting first page of all enterprise apps")
        # result = await self.graph_client.users.get()
        result = await self.graph_client.applications.get()
        users.extend(result.value)
        # Pagination if next_link is present
        while result.odata_next_link:
            logger.debug("Getting next page of all enterprise apps")
            result = await self.graph_client.applications.with_url(
                result.odata_next_link
            ).get()
            users.extend(result.value)
        return users
