from typing import List

from models.Models import UsecaseTypeModel
from services.CosmosDBService import CosmosDBService
from services.ABCUsecaseService import UsecaseService


class UsecaseTypeService(UsecaseService):
    @property
    def fields(self) -> List[str]:
        return ["id", "name_de", "name_en", "indices", "features"]

    async def get(self):
        items = await CosmosDBService(
            database=self._DATABASE, container=self._CONTAINER
        ).query(
            query=f"Select d.{',d.'.join(self.fields)} from {self._CONTAINER} d"
        )  # fields=self.fields, params=[])
        usecasetypes = [UsecaseTypeModel(**item) for item in items]
        return usecasetypes
