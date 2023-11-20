from abc import ABC, abstractmethod
from enum import Enum
from typing import List, TypeVar, Generic
from collections.abc import Mapping

from models.Models import CognitiveSearchEmbeddingModel, CognitiveSearchModel
from strategies.ABCContext import AbstractContext


_CognitiveSearchModel = TypeVar(
    "_CognitiveSearchModel", CognitiveSearchEmbeddingModel, CognitiveSearchModel
)


class CognitiveSearchIndexContext(AbstractContext):
    def __init__(self, strategy: "AbstractCognitiveSearchIndexStrategy"):
        self._strategy = strategy

    def create_index_model(self, **kwargs) -> _CognitiveSearchModel:
        return self._strategy.create_index_model(**kwargs)


class AbstractCognitiveSearchIndexStrategy(ABC):
    @abstractmethod
    def create_index_model(self, **kwargs) -> _CognitiveSearchModel:
        ...


class CognitiveSearchIndexWEmbeddingsStrategy(AbstractCognitiveSearchIndexStrategy):
    def create_index_model(self, **kwargs) -> CognitiveSearchEmbeddingModel:
        id = kwargs.pop("id")
        content = kwargs.pop("content")
        category_id = kwargs.pop("category_id")
        sourcepage = kwargs.pop("sourcepage")
        sourcefile = kwargs.pop("sourcefile")
        embedding = kwargs.pop("embedding")
        return CognitiveSearchEmbeddingModel(
            id=id,
            content=content,
            category_id=category_id,
            sourcepage=sourcepage,
            sourcefile=sourcefile,
            embedding=embedding,
        )


class CognitiveSearchIndexStandardStrategy(AbstractCognitiveSearchIndexStrategy):
    def create_index_model(self, **kwargs) -> CognitiveSearchModel:
        id = kwargs.pop("id")
        content = kwargs.pop("content")
        category_id = kwargs.pop("category_id")
        sourcepage = kwargs.pop("sourcepage")
        sourcefile = kwargs.pop("sourcefile")
        return CognitiveSearchModel(
            id=id,
            content=content,
            category_id=category_id,
            sourcepage=sourcepage,
            sourcefile=sourcefile,
        )


class Indices(Enum):
    GPTKBINDEX = "gptkbindex"
    GPTKBINDEX_WO_EMBD = "gptkbindex-woe"


class IndexStrategyMapping(Mapping):
    _mapping = {
        Indices.GPTKBINDEX.value: CognitiveSearchIndexContext(
            strategy=CognitiveSearchIndexWEmbeddingsStrategy()
        ),
        Indices.GPTKBINDEX_WO_EMBD.value: CognitiveSearchIndexContext(
            strategy=CognitiveSearchIndexStandardStrategy()
        ),
    }

    def __getitem__(self, key):
        return self._mapping[key]

    def __iter__(self):
        return iter(self._mapping)

    def __len__(self):
        return len(self._mapping)


class CognitiveSearchIndexStrategyProvider:
    @staticmethod
    def get_context(strat: str) -> CognitiveSearchIndexContext:
        return IndexStrategyMapping()[strat]
