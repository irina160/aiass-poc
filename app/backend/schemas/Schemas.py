from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from schemas.BaseSchemas import BaseSchema


@dataclass
class BaseDeleteSchema(BaseSchema):
    id: str


@dataclass
class FileDeleteSchema(BaseSchema):
    id: str


@dataclass
class FileBase64Schema(BaseSchema):
    id: str
    name: str
    data: str


@dataclass
class CategorySchema(BaseSchema):
    id: str
    name_de: str
    name_en: str
    description_de: str
    description_en: str
    system_prompt: str
    temperature: str
    model: str
    files: List[FileBase64Schema]


@dataclass
class CategoryUpdateSchema(CategorySchema):
    filesToDelete: List[FileDeleteSchema]


@dataclass
class IndexSchema(BaseSchema):
    id: str
    name_de: str
    name_en: str
    description_de: str
    description_en: str
    logo: str
    categories: Optional[List[CategorySchema]] = field(default_factory=list)


@dataclass
class Settings:
    ...


@dataclass
class Features(BaseSchema):
    general: Dict[str, Settings]
    indices: Dict[str, Settings]
    categories: Dict[str, Settings]
    chat: Dict[str, Settings]
    overrides: Dict[str, Settings]


@dataclass
class UseCaseTypeSchema(BaseSchema):
    id: str
    name_de: str
    name_en: str
    features: Dict[str, Dict[str, Dict[str, str]]]
    indices: Optional[List[IndexSchema]] = field(default_factory=list)


@dataclass
class TemperatureSchema(BaseSchema):
    id: str
    display_name_de: str
    display_name_en: str
    temperature: int


@dataclass
class ModelSchema(BaseSchema):
    id: str
    display_name_de: str
    display_name_en: str
    model: str


@dataclass
class HistorySchema(BaseSchema):
    user: str


@dataclass
class OverridesSchema(BaseSchema):
    retrieval_mode: str
    semantic_captions: bool
    semantic_ranker: bool
    suggest_followup_questions: bool
    top: int


@dataclass
class ChatSchema(BaseSchema):
    approach: str
    history: List[HistorySchema]
    overrides: OverridesSchema


@dataclass
class PromptSchema(BaseSchema):
    type: str
    content: str
