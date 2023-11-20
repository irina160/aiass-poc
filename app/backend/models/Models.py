from dataclasses import dataclass, field
import io
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union
from models.BaseModels import BaseModel


"""
CognitiveSearchModels
"""


@dataclass
class CognitiveSearchModel(BaseModel):
    id: str
    content: str
    category_id: str
    sourcepage: str
    sourcefile: str


@dataclass
class CognitiveSearchEmbeddingModel(CognitiveSearchModel):
    embedding: List[float]


"""
PageModels
"""


@dataclass
class PageCosmosDBModel(BaseModel):
    page_no: int
    page_path: str


@dataclass
class PageBlobStorageModel(BaseModel):
    data: bytes
    path: str
    metadata: Optional[Dict[str, str]] = field(default_factory=dict)
    tags: Optional[Dict[str, str]] = field(default_factory=dict)


"""
FileModels
"""

F = TypeVar("F", bytes, str)


@dataclass
class FileModel(BaseModel, Generic[F]):
    id: str
    data: F
    name: str


@dataclass
class FileBlobStorageModel(BaseModel):
    data: bytes
    path: str
    pages: List[PageBlobStorageModel]
    metadata: Optional[Dict[str, str]] = field(default_factory=dict)
    tags: Optional[Dict[str, str]] = field(default_factory=dict)


@dataclass
class FileCosmosDBModel(BaseModel):
    id: str
    name: str
    path: str
    pages: List[PageCosmosDBModel] = field(default_factory=list)


@dataclass
class FileDeleteModel(BaseModel):
    id: str


"""
CategoryModels / Base
"""


@dataclass
class BaseCategoryModel(BaseModel):
    id: str
    name_de: str
    name_en: str
    description_de: str
    description_en: str
    system_prompt: str
    temperature: str
    model: str


@dataclass
class CategoryCosmosDBModel(BaseCategoryModel):
    files: List[FileCosmosDBModel] = field(default_factory=list)


@dataclass
class CategoryModel(BaseCategoryModel):
    filesToDelete: List[FileDeleteModel] = field(default_factory=list)
    files: List[FileModel] = field(default_factory=list)


"""
IndexModels
"""


@dataclass
class BaseIndexModel(BaseModel):
    id: str
    name_de: str
    name_en: str
    description_de: str
    description_en: str


@dataclass
class IndexModel(BaseIndexModel):
    categories: List[CategoryModel] = field(default_factory=list)


@dataclass
class IndexCosmosDBModel(BaseIndexModel):
    categories: List[CategoryCosmosDBModel] = field(default_factory=list)


"""
/***********************
****** UsecaseType *****
************************/
"""


@dataclass
class UsecaseTypeModel(BaseModel):
    id: str
    name_de: str
    name_en: str
    features: Dict[str, Dict[str, Dict[str, str]]]
    indices: List[IndexModel] = field(default_factory=list)

    def retrieve_props_for_post(self) -> Dict[str, str]:
        return {"id": self.id, "name_de": self.name_de, "name_en": self.name_en}


@dataclass
class TemperatureModel(BaseModel):
    id: str
    display_name_de: str
    display_name_en: str
    temperature: int

    def retrieve_props_for_post(self) -> Dict[str, str]:
        return {
            "id": self.id,
            "display_name_de": self.display_name_de,
            "display_name_en": self.display_name_en,
        }


@dataclass
class ModelModel(BaseModel):
    id: str
    display_name_de: str
    display_name_en: str
    model: str

    def retrieve_props_for_post(self) -> Dict[str, str]:
        return {
            "id": self.id,
            "display_name_de": self.display_name_de,
            "display_name_en": self.display_name_en,
        }


@dataclass
class HistoryModel(BaseModel):
    user: str


@dataclass
class OverridesModel(BaseModel):
    retrieval_mode: str
    semantic_captions: bool
    semantic_ranker: bool
    suggest_followup_questions: bool
    top: int


@dataclass
class ChatModel(BaseModel):
    approach: str
    history: List[HistoryModel]
    overrides: OverridesModel


@dataclass
class PromptModel(BaseModel):
    type: str
    content: str
