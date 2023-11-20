from typing import Dict, List, Tuple, Union
from quart import current_app
from services.ABCAzureService import AbstractAzureService
from azure.storage.blob.aio import BlobServiceClient, ContainerClient, BlobClient
from azure.storage.blob import ContainerProperties, FilteredBlob
import io
from functools import singledispatchmethod
from models.Models import FileBlobStorageModel
import asyncio

CONFIG_BLOB_CLIENT = "blob_client"


class BlobService(AbstractAzureService):
    MAX_NUMBER_OF_DELETE_BLOBS = 256

    @property
    def client(self) -> BlobServiceClient:
        return current_app.config[CONFIG_BLOB_CLIENT]

    @client.setter
    def client(self):
        raise Exception("You are not allowed to set the client")

    def __init__(self, create_container: bool = False):
        self._create = create_container

    async def __check_for_container(self, container_client: ContainerClient):
        if not await container_client.exists():
            if not self._create:
                raise ValueError(
                    f"The provided container {container_client.container_name} does not exist. Either make sure it exists or set create = True in init"
                )
            else:
                await container_client.create_container()

    async def upload(
        self,
        container: Union[ContainerProperties, str],
        name: str,
        data: Union[bytes, io.BytesIO],
        metadata: Dict[str, str] | None = None,
        tags: Dict[str, str] | None = None,
    ) -> BlobClient:
        container_client = self.client.get_container_client(container)
        await self.__check_for_container(container_client)
        upload_result = await container_client.upload_blob(
            name=name, data=data, metadata=metadata, tags=tags, overwrite=True  # type: ignore
        )
        return upload_result

    @singledispatchmethod
    async def bulk_upload(self, files, container: Union[ContainerProperties, str]):
        raise NotImplementedError("Not yet implemented")

    @bulk_upload.register
    async def _(
        self, files: FileBlobStorageModel, container: Union[ContainerProperties, str]
    ) -> Tuple[
        BlobClient, List[BlobClient]
    ]:  # TODO: This method is not ideal. Also the BlobService shouldnt contain business logic. Refactor
        async with asyncio.TaskGroup() as tg:
            file_info = tg.create_task(
                self.upload(
                    container=container,
                    name=files.path,
                    data=files.data,
                    metadata=files.metadata,
                    tags=files.tags,
                )
            )
            page_infos: List[asyncio.Task[BlobClient]] = []
            for page in files.pages:
                page_info = tg.create_task(
                    self.upload(
                        container=container,
                        name=page.path,
                        data=page.data,
                        metadata=page.metadata,
                        tags=page.tags,
                    )
                )
                page_infos.append(page_info)
        file_info_result = file_info.result()
        page_infos_result = [_page_info.result() for _page_info in page_infos]
        return (file_info_result, page_infos_result)

    async def batch_upload(self):
        raise NotImplementedError("Not yet implemented")

    async def remove_blob(
        self, container: Union[ContainerProperties, str], blob: str
    ) -> None:
        container_client = self.client.get_container_client(container)
        await container_client.delete_blob(blob=blob)

    async def remove_blobs(
        self, container: Union[ContainerProperties, str], blobs: List[str]
    ) -> None:
        container_client = self.client.get_container_client(container=container)
        i = 0
        batch: List[str] = []
        for blob in blobs:
            batch.append(blob)
            i += 1
            if i % self.MAX_NUMBER_OF_DELETE_BLOBS == 0:
                await container_client.delete_blobs(*batch)
                batch = []
        if len(batch) > 0:
            await container_client.delete_blobs(*batch)

    async def find_blob_by_tags(
        self, container: Union[ContainerProperties, str], query: str
    ) -> List[FilteredBlob]:
        container_client = self.client.get_container_client(container=container)
        blob_list = container_client.find_blobs_by_tags(filter_expression=query)
        blobs = [blob async for blob in blob_list]
        return blobs
