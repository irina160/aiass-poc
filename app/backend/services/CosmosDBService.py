import asyncio
from typing import Any, Dict, List, Union

from quart import current_app
from azure.cosmos.aio import CosmosClient
from services.ABCAzureService import AbstractAzureService

CONFIG_COSMOSDB_CLIENT = "cosmosdb_client"


class CosmosDBService(AbstractAzureService):
    @property
    def client(self) -> CosmosClient:
        return current_app.config[CONFIG_COSMOSDB_CLIENT]

    @client.setter
    def client(self):
        raise Exception("You are not allowed to set the client")

    def __init__(self, database: str, container: str):
        self.database_name = database
        self.container_name = container
        database_proxy = self.client.get_database_client(self.database_name)
        container_proxy = database_proxy.get_container_client(self.container_name)
        self.container = container_proxy

    async def query(
        self,
        query: str,
        params: Union[List[Dict[str, str]], None] = None,
    ):
        aitems = self.container.query_items(query=query, parameters=params)
        items = [item async for item in aitems]
        return items

    def read(self):
        ...

    async def patch(
        self, item_id: str, partition_key: str, patch: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        patched_item = await self.container.patch_item(
            item=item_id, partition_key=partition_key, patch_operations=patch
        )
        return patched_item

    async def batch_patch(
        self, item_id: str, partition_key: str, patch_operations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        i = 0
        batch: List[Dict] = []
        for patch_operation in patch_operations:
            batch.append(patch_operation)
            i += 1
            if i % 10 == 0:
                result = await self.patch(item_id, partition_key, patch=batch)
                batch = []

        if len(batch) > 0:
            result = await self.patch(item_id, partition_key, patch=batch)
        return result  # type: ignore

    async def delete(self, item_id: str, partition_key: str, **kwargs):
        # TODO: Add try except
        await self.container.delete_item(
            item=item_id, partition_key=partition_key, **kwargs
        )

    async def bulk_delete(self, item_ids: List[str], partition_keys: List[str]):
        async with asyncio.TaskGroup() as tg:
            [
                tg.create_task(
                    self.delete(item_id=item_id, partition_key=partition_key)
                )
                for item_id, partition_key in list(zip(item_ids, partition_keys))
            ]

    async def create_item(self, body: Dict, **kwargs) -> Dict:
        """
        Create an item in the container.

        Args:
            body (Dict): A dict-like object representing the item to create.
            kwargs: see ContainerProxy.create_item

        Returns:
            Dict: A dict representing the new item.
        """
        new_item = await self.container.create_item(body=body, **kwargs)
        return new_item
