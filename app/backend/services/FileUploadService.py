from dataclasses import dataclass
import io
import asyncio
from typing import Dict, List, Optional
from services.BlobService import BlobService
from azure.storage.blob.aio import BlobClient


@dataclass
class BlobUploadArgs:
    container: str
    name: str
    data: io.BytesIO
    metadata: Optional[Dict[str, str]]
    tags: Optional[Dict[str, str]]


class FileUploadService:
    @staticmethod
    async def upload_to_blob(item: BlobUploadArgs) -> BlobClient:
        upload_item = await BlobService().upload(
            container=item.container,
            name=item.name,
            data=item.data,
            metadata=item.metadata,
            tags=item.tags,
        )
        return upload_item

    @staticmethod
    async def bulk_upload_to_blob(items: List[BlobUploadArgs]) -> List[BlobClient]:
        async with asyncio.TaskGroup() as tg:
            upload_infos: List[asyncio.Task[BlobClient]] = []
            for item in items:
                upload_info = tg.create_task(FileUploadService.upload_to_blob(item))
                upload_infos.append(upload_info)
        upload_results = [x.result() for x in upload_infos]
        return upload_results
