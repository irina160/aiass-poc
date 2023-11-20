from typing import Any, Dict, List
from quart import current_app
from services.ABCAzureService import AbstractAzureService
from azure.search.documents.aio import SearchClient
from azure.search.documents.models import IndexingResult
from models.Models import CognitiveSearchEmbeddingModel

from multimethod import multimethod as singledispatchmethod

CONFIG_SEARCH_CLIENT = "search_client"


class CognitiveSearchService(AbstractAzureService):
    MAX_NUMBER_OF_DOCUMENTS = 1000

    @property
    def client(self) -> SearchClient:
        return current_app.config[CONFIG_SEARCH_CLIENT]

    @client.setter
    def client(self):
        raise Exception("You are not allowed to set the client")

    def __init__(self):
        ...

    async def index(self, documents: List[Dict]) -> List[IndexingResult]:
        """
        Can be any List of documents to index. For high amounts of documents use CognitiveSearchService@batch_index

        Args:
            document (_type_): _description_

        Returns:
            List[IndexingResult]: _description_
        """
        indexing_result = await self.client.upload_documents(documents=documents)
        return indexing_result

    async def batch_index(self, documents: List[Dict]) -> List[IndexingResult]:
        i = 0
        results: List[IndexingResult] = []
        batch: List[Dict] = []
        for doc in documents:
            batch.append(doc)
            i += 1
            if i % self.MAX_NUMBER_OF_DOCUMENTS == 0:
                results_ = await self.index(documents=batch)
                succeeded = sum([1 for r in results if r.succeeded])
                batch = []
                results.extend(results_)

        if len(batch) > 0:
            results_ = await self.index(documents=batch)
            succeeded = sum([1 for r in results if r.succeeded])
            results.extend(results_)
        return results

    async def search(self, **kwargs) -> List[Dict]:
        """
        Have a look at SearchClient@search for a list of possible arguments

        Returns:
            List[Dict]: _description_
        """
        aitems = await self.client.search(**kwargs)
        items = [item async for item in aitems]
        return items

    async def delete_document(self, documents: List[Dict]) -> None:
        await self.client.delete_documents(documents=documents)
