from abc import ABC, abstractmethod
from typing import Dict, List, Union

"""
COSMOSDB_DATABASE_DEMO = "Demo"
COSMOSDB_CONTAINER_USECASEDEFINITION = "UseCaseDefinition"
"""
AZURE_STORAGE_CONTAINER = "content"
AZURE_COSMOS_DB = "Demo"
AZURE_COSMOS_CONTAINER = "UseCaseDefinition"


class AbstractUsecaseService(ABC):
    @property
    @abstractmethod
    def _DATABASE(self):
        ...

    @property
    @abstractmethod
    def _CONTAINER(self):
        ...

    @property
    @abstractmethod
    def _STORAGE_CONTAINER(self):
        ...

    @_DATABASE.setter
    def _DATABASE(self):
        ...

    @_CONTAINER.setter
    def _CONTAINER(self):
        ...

    @_STORAGE_CONTAINER.setter
    def _STORAGE_CONTAINER(self):
        ...


class UsecaseService(AbstractUsecaseService):
    @property
    def _DATABASE(self):
        return AZURE_COSMOS_DB

    @property
    def _CONTAINER(self):
        return AZURE_COSMOS_CONTAINER

    @property
    def _STORAGE_CONTAINER(self):
        return AZURE_STORAGE_CONTAINER

    @_DATABASE.setter
    def _DATABASE(self):
        raise Exception("You are not allowed to set the Database")

    @_CONTAINER.setter
    def _CONTAINER(self):
        raise Exception("You are not allowed to set the Container")

    @_STORAGE_CONTAINER.setter
    def _STORAGE_CONTAINER(self):
        raise Exception("You are not allowed to set the Storage Container")
