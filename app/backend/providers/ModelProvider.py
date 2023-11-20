from abc import ABC, abstractmethod
from enum import Enum
import json
from typing import TypeVar
import uuid
from werkzeug.datastructures import MultiDict

from quart import Request
from models.Models import FileModel, IndexModel, CategoryModel, UsecaseTypeModel
from utils import create_dataclass_from_dict

_T = TypeVar("_T", IndexModel, CategoryModel, UsecaseTypeModel)


class SupportedFormDataModels(Enum):
    IndexModel = IndexModel
    CategoryModel = CategoryModel
    UsecaseTypeModel = UsecaseTypeModel


class SupportedModelTypes(Enum):
    Index = "index"
    Category = "category"


class AbstractModelTypeFactory(ABC):
    @abstractmethod
    def create_str_model(self, **kwargs) -> _T:
        ...

    @abstractmethod
    def create_bytes_model(self, **kwargs) -> _T:
        ...


class AbstractIndexModelFactory(AbstractModelTypeFactory):
    @abstractmethod
    def create_str_model(self, **kwargs) -> IndexModel:
        ...

    @abstractmethod
    def create_bytes_model(self, **kwargs) -> IndexModel:
        ...


class IndexModelFactory(AbstractIndexModelFactory):
    def create_bytes_model(self, **kwargs) -> IndexModel:
        files = kwargs.pop("files")
        form = kwargs.pop("form")
        files_ = MultiDict()
        for category in files.keys():
            category_id = category.split("<")[1].split(">")[0]
            for file in files.getlist(category):
                data = file.read()
                files_.add(
                    category_id,
                    [
                        ("data", data),
                        ("name", file.filename),
                        ("id", str(uuid.uuid1())),
                    ],
                )

        new_multidict = MultiDict()
        new_multidict.add(
            "index",
            (
                "id",
                list(filter(lambda x: x.startswith("index"), list(form.keys())))[0]
                .split("<")[1]
                .split(">")[0],
            ),
        )
        for key, val in form.items():
            prop = key.split(":")[1]
            rest = key.split(":")[0]
            if "index" in key:
                new_multidict.add("index", (prop, val))
            elif "category" in key:
                new_multidict.add(rest, (prop, val))

        categories = []
        for key in new_multidict.keys():
            vals = new_multidict.getlist(key)
            if "category" in key:
                id = key.split("<")[1].split(">")[0]
                files_data = list(map(lambda x: dict(x), files_.getlist(id)))
                vals.append(("id", id))
                category = dict(vals)
                category["files"] = files_data
                categories.append(category)

        index = dict(new_multidict.getlist("index"))
        index["categories"] = categories
        model = create_dataclass_from_dict(IndexModel, index)
        return model

    def create_str_model(self, **kwargs) -> IndexModel:
        dict_ = kwargs.pop("dict_")
        return create_dataclass_from_dict(IndexModel, dict_)


class AbstractCategoryModelFactory(AbstractModelTypeFactory):
    @abstractmethod
    def create_str_model(self) -> CategoryModel:
        ...

    @abstractmethod
    def create_bytes_model(self, **kwargs) -> CategoryModel:
        ...


class CategoryModelFactory(AbstractCategoryModelFactory):
    def create_bytes_model(self, **kwargs) -> CategoryModel:
        files = kwargs.pop("files")
        form = kwargs.pop("form")
        files_ = []
        for file in files.getlist(list(files.keys())[0]):
            if file.filename:
                data = file.read()
                files_.append(
                    FileModel[bytes](
                        id=str(uuid.uuid1()), data=data, name=file.filename
                    ).jsonify()
                )
            else:
                continue

        new_multidict = MultiDict()
        new_multidict.add(
            "category",
            (
                "id",
                list(filter(lambda x: x.startswith("category"), list(form.keys())))[0]
                .split("<")[1]
                .split(">")[0],
            ),
        )
        for key, val in form.items():
            prop = key.split(":")[1]
            rest = key.split(":")[0]
            if "filesToDelete" in key:
                val = json.loads(val)
            new_multidict.add("category", (prop, val))

        category = dict(new_multidict.getlist("category"))
        category["files"] = files_
        return create_dataclass_from_dict(CategoryModel, category)

    def create_str_model(self, **kwargs) -> CategoryModel:
        dict_ = kwargs.pop("dict_")
        model = create_dataclass_from_dict(CategoryModel, dict_)
        return model


class AbstractModelFactory(ABC):
    @abstractmethod
    def create_index() -> IndexModelFactory:
        ...

    @abstractmethod
    def create_category() -> CategoryModelFactory:
        ...


class ModelFactory(AbstractModelFactory):
    def create_index(self):
        return IndexModelFactory()

    def create_category(self):
        return CategoryModelFactory()


class ModelProvider:
    @staticmethod
    async def from_request(request: Request, schema: SupportedModelTypes) -> _T:
        factory_provider = ModelFactory()
        model_factory = ModelProvider._determine_model_type(
            schema=schema, factory=factory_provider
        )
        match request.mimetype:
            case "application/json":
                return await ModelProvider.handle_json_request(request, model_factory)
            case "multipart/form-data":
                return await ModelProvider.handle_form_data(request, model_factory)
            case "application/octet-stream":
                raise NotImplementedError("Not yet implemented")
            case _:
                raise NotImplementedError("Not yet implemented")

    @staticmethod
    def _determine_model_type(
        schema: SupportedModelTypes, factory: AbstractModelFactory
    ):
        match schema:
            case SupportedModelTypes.Index:
                return factory.create_index()
            case SupportedModelTypes.Category:
                return factory.create_category()
            case _:
                raise Exception("This Datatype does not exist.")

    @staticmethod
    async def handle_json_request(
        request: Request, model_factory: AbstractModelTypeFactory
    ) -> _T:
        req_json = await request.json
        model = model_factory.create_str_model(dict_=req_json)
        return model

    @staticmethod
    async def handle_form_data(
        request: Request, model_factory: AbstractModelTypeFactory
    ) -> _T:
        files = await request.files
        form = await request.form
        model = model_factory.create_bytes_model(files=files, form=form)
        return model
