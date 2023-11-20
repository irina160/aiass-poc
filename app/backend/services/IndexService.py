import asyncio
import copy
from typing import Any, Dict, List, Tuple
from utils import create_dataclass_from_dict

from models.Models import (
    CategoryCosmosDBModel,
    IndexModel,
    IndexCosmosDBModel,
    CategoryModel,
)

from services.ABCUsecaseService import (
    UsecaseService,
)
from services.CosmosDBService import CosmosDBService
from services.CategoryService import CategoryService


class IndexService(UsecaseService):
    @property
    def fields(self):
        return [
            "id",
            "name_de",
            "name_en",
            "description_de",
            "description_en",
            "logo",
            "categories",
        ]

    async def __query_indices_from_db(
        self, usecasetype_id: str
    ) -> List[Dict[str, Any]]:
        items = await CosmosDBService(
            database=self._DATABASE, container=self._CONTAINER
        ).query(
            query=f"Select t.{',t.'.join(self.fields)} from {self._CONTAINER} d JOIN t in d.indices where d.id=@usecasetypeid",
            params=[{"name": "@usecasetypeid", "value": usecasetype_id}],
        )
        return items

    async def get(self, usecasetype_id: str):
        items = await self.__query_indices_from_db(usecasetype_id=usecasetype_id)
        indices = [
            create_dataclass_from_dict(IndexCosmosDBModel, item) for item in items
        ]
        return indices

    async def post(self, index: IndexModel, usecasetype_id: str):
        index_wo_cat = copy.deepcopy(index)
        index_wo_cat.categories = []
        index_update = await self.__upload_index(
            index=index_wo_cat, usecasetype_id=usecasetype_id
        )
        if index.categories:
            await self.__upload_categories(
                categories=index.categories,
                usecasetype_id=usecasetype_id,
                index_id=index.id,
                index_idx=len(index_update) - 1,
            )
        return index_update

    async def __upload_categories(
        self,
        categories: List[CategoryModel],
        usecasetype_id: str,
        index_id: str,
        index_idx: int,
    ):
        async with asyncio.TaskGroup() as tg:
            for category in categories:
                tg.create_task(
                    CategoryService().post(
                        category,
                        usecasetype_id=usecasetype_id,
                        index_id=index_id,
                        index_idx=index_idx,
                    )
                )

    async def __upload_index(self, index: IndexModel, usecasetype_id: str):
        cdb_service = CosmosDBService(
            database=self._DATABASE, container=self._CONTAINER
        )
        patch = [{"op": "add", "path": "/indices/-", "value": index.jsonify()}]
        items = await cdb_service.patch(usecasetype_id, usecasetype_id, patch=patch)
        indices = [
            create_dataclass_from_dict(IndexCosmosDBModel, item)
            for item in items["indices"]
        ]
        return indices

    async def put(
        self, index: IndexModel, usecasetype_id: str
    ) -> List[IndexCosmosDBModel]:  # TODO: rename to singular update_item
        current_index_idx, current_index = await self.get_current_index_and_idx(
            id=index.id, usecasetype_id=usecasetype_id
        )
        if current_index_idx is None:
            raise Exception("Something went wrong")
        patch = [
            {
                "op": "set",
                "path": f"/indices/{current_index_idx}/name_de",
                "value": index.name_de,
            },
            {
                "op": "set",
                "path": f"/indices/{current_index_idx}/name_en",
                "value": index.name_en,
            },
            {
                "op": "set",
                "path": f"/indices/{current_index_idx}/description_en",
                "value": index.description_en,
            },
            {
                "op": "set",
                "path": f"/indices/{current_index_idx}/description_de",
                "value": index.description_de,
            },
        ]

        cdb_service = CosmosDBService(
            database=self._DATABASE, container=self._CONTAINER
        )
        items = await cdb_service.patch(
            item_id=usecasetype_id, partition_key=usecasetype_id, patch=patch
        )
        indices = [
            create_dataclass_from_dict(IndexCosmosDBModel, item)
            for item in items["indices"]
        ]
        return indices

    async def get_current_index_and_idx(
        self, id: str, usecasetype_id: str
    ) -> Tuple[int, IndexCosmosDBModel]:
        items = await self.__query_indices_from_db(usecasetype_id=usecasetype_id)
        indices = [
            create_dataclass_from_dict(IndexCosmosDBModel, item) for item in items
        ]
        current_index_and_idx = next(
            ((i, item) for i, item in enumerate(indices) if item.id == id), None
        )
        if current_index_and_idx is None:
            raise Exception(f"Could not find index with id {id}")
        else:
            return current_index_and_idx

    async def delete(self, id: str, usecasetype_id: str) -> List[IndexCosmosDBModel]:
        idx, index = await self.get_current_index_and_idx(
            id=id, usecasetype_id=usecasetype_id
        )
        if index.categories:
            await self.__delete_categories(
                categories=index.categories,
                usecasetype_id=usecasetype_id,
                index_idx=idx,
            )

        patch = [{"op": "remove", "path": f"/indices/{idx}"}]
        cdb_service = CosmosDBService(
            database=self._DATABASE, container=self._CONTAINER
        )
        items = await cdb_service.patch(
            item_id=usecasetype_id, partition_key=usecasetype_id, patch=patch
        )
        indices = [
            create_dataclass_from_dict(IndexCosmosDBModel, item)
            for item in items["indices"]
        ]
        return indices

    async def __delete_categories(
        self,
        categories: List[CategoryCosmosDBModel],
        usecasetype_id: str,
        index_idx: int,
    ) -> None:
        for category in categories:
            await CategoryService().delete(
                id=category.id,
                usecasetype_id=usecasetype_id,
                index_idx=index_idx,
            )
