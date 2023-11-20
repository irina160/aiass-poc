from abc import ABC, abstractmethod
import asyncio
import os
from typing import Any, Dict, List, Tuple, Union
import uuid
import openai
from quart import current_app

from tenacity import retry, stop_after_attempt, wait_random_exponential
from services.ChatHistoryService import ChatHistoryService
from strategies.CognitiveSearchIndexStrategy import (
    CognitiveSearchIndexStrategyProvider,
)

from models.Models import (
    CategoryModel,
    CognitiveSearchEmbeddingModel,
    CognitiveSearchModel,
    FileModel,
    FileCosmosDBModel,
    PageCosmosDBModel,
    CategoryCosmosDBModel,
    IndexCosmosDBModel,
)

from services.ABCUsecaseService import (
    UsecaseService,
)

from azure.storage.blob.aio import BlobClient

from services.BlobService import BlobService
from services.FileManagementService import (
    FileManagementService,
    ByteFileManagementStrategy,
    StrFileManagementStrategy,
)
from services.FormRecognizerService import FormRecognizerService, PREBUILTLAYOUT
from services.TextManagementService import FormRecognizerTextManagementService
from services.CognitiveSearchService import CognitiveSearchService
from services.CosmosDBService import CosmosDBService

from utils import create_dataclass_from_dict


class CategoryService(UsecaseService):
    MAX_DB_PATCH_OPERATIONS = 10

    @property
    def fields(self):
        return [
            "id",
            "name_en",
            "name_de",
            "description_en",
            "description_de",
            "system_prompt",
            "temperature",
            "model",
            "files",
        ]

    async def __query_categories_from_db(
        self, usecasetype_id: str, index_id: str
    ) -> List[Dict[str, Any]]:
        items = await CosmosDBService(
            database=self._DATABASE, container=self._CONTAINER
        ).query(
            query=f"Select c.{',c.'.join(self.fields)} FROM {self._CONTAINER} d JOIN t in d.indices JOIN c in t.categories where d.id=@usecasetypeid and t.id=@indexid",
            params=[
                {"name": "@usecasetypeid", "value": usecasetype_id},
                {"name": "@indexid", "value": index_id},
            ],
        )
        return items

    async def __get_index_by_idx(
        self, usecasetype_id: str, index_idx: int
    ) -> IndexCosmosDBModel:
        cdb_service = CosmosDBService(
            database=self._DATABASE, container=self._CONTAINER
        )
        items = await cdb_service.query(
            query=f"Select * from {self._CONTAINER} d where d.id=@id",
            params=[{"name": "@id", "value": usecasetype_id}],
        )
        indices = [
            create_dataclass_from_dict(IndexCosmosDBModel, item)
            for item in items[0]["indices"]
        ]
        return indices[index_idx]

    async def __find_current_category(
        self, id: str, usecasetype_id: str, index_idx: int
    ) -> Tuple[int, CategoryCosmosDBModel]:
        index = await self.__get_index_by_idx(
            usecasetype_id=usecasetype_id, index_idx=index_idx
        )
        current_category_idx = next(
            ((i, item) for i, item in enumerate(index.categories) if item.id == id), None  # type: ignore
        )
        if current_category_idx is None:
            raise Exception(f"Could not find category with id: {id}")
        return current_category_idx

    async def __delete_from_blob(
        self, files: Union[List[FileCosmosDBModel], List[str]]
    ):
        file_ids = files
        if all(isinstance(file, FileCosmosDBModel) for file in files):
            file_ids = [file.id for file in files]  # type: ignore
        queries = [f"\"id\" = '{file_id}'" for file_id in file_ids]
        blb_service = BlobService()
        blob_lists = [
            await blb_service.find_blob_by_tags(self._STORAGE_CONTAINER, query=query)
            for query in queries
        ]
        blob_names = list(map(lambda x: x.name, sum(blob_lists, [])))
        await blb_service.remove_blobs(
            container=self._STORAGE_CONTAINER, blobs=blob_names
        )

    async def __delete_cat_from_cog_search(self, category_id: str):
        filter = f"category_id eq '{category_id}'"
        await self.__delete_from_cog_search(filter=filter)

    async def __delete_file_from_cog_search(self, file_id: str):
        filter = f"search.ismatch('{file_id}*', 'id')"
        await self.__delete_from_cog_search(filter=filter)

    async def __delete_from_cog_search(self, filter: str):
        cogsearch_service = CognitiveSearchService()
        while True:
            items = await cogsearch_service.search(
                search_text="", filter=filter, top=1000, include_total_count=True
            )
            if items:
                await cogsearch_service.delete_document(
                    documents=[{"id": item["id"]} for item in items]
                )
            else:
                break

    async def __delete_cat_from_db(
        self, usecasetype_id: str, index_idx: int, category_idx: int
    ) -> Dict[str, Any]:
        patch = [
            {
                "op": "remove",
                "path": f"/indices/{index_idx}/categories/{category_idx}",
            }
        ]
        items = await self.__patch_db(usecasetype_id=usecasetype_id, patch=patch)
        return items

    async def __delete_files_from_db(
        self,
        usecasetype_id: str,
        index_idx: int,
        category_idx: int,
        file_idxs: List[int],
    ):
        patch = [
            {
                "op": "remove",
                "path": f"/indices/{index_idx}/categories/{category_idx}/files/{file_idx}",
            }
            for file_idx in file_idxs
        ]
        items = await self.__patch_db(usecasetype_id=usecasetype_id, patch=patch)
        return items

    # TODO: Have a look if this can be done more elegantly
    async def __patch_db(
        self, usecasetype_id: str, patch: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        cdb_service = CosmosDBService(
            database=self._DATABASE, container=self._CONTAINER
        )
        if len(patch) > self.MAX_DB_PATCH_OPERATIONS:
            indices = await cdb_service.batch_patch(
                item_id=usecasetype_id,
                partition_key=usecasetype_id,
                patch_operations=patch,
            )
        else:
            indices = await cdb_service.patch(
                item_id=usecasetype_id, partition_key=usecasetype_id, patch=patch
            )
        return indices

    async def get(
        self, usecasetype_id: str, index_id: str
    ) -> List[CategoryCosmosDBModel]:
        items = await self.__query_categories_from_db(
            usecasetype_id=usecasetype_id, index_id=index_id
        )
        categories = [
            create_dataclass_from_dict(CategoryCosmosDBModel, item) for item in items
        ]
        return categories

    async def delete(
        self, id: str, usecasetype_id: str, index_idx: int
    ) -> List[CategoryCosmosDBModel]:
        idx, category = await self.__find_current_category(
            id=id, usecasetype_id=usecasetype_id, index_idx=index_idx
        )
        await self.__delete_from_blob(category.files)
        await self.__delete_cat_from_cog_search(category_id=id)
        await ChatHistoryService.delete_chat_history_by_category(id)
        indices = await self.__delete_cat_from_db(
            usecasetype_id=usecasetype_id, index_idx=index_idx, category_idx=idx
        )
        categories = [
            create_dataclass_from_dict(CategoryCosmosDBModel, item)
            for item in indices["indices"][index_idx]["categories"]
        ]
        return categories

    # TODO: Refactor this
    @retry(wait=wait_random_exponential(min=1, max=5), stop=stop_after_attempt(6))
    async def __create_embeddings(self, input: str) -> List[float]:
        AZURE_OPENAI_EMB_DEPLOYMENT = os.getenv(
            "AZURE_OPENAI_EMB_DEPLOYMENT", "embedding"
        )
        AZURE_OPENAI_EMB_MODEL = os.getenv(
            "AZURE_OPENAI_EMB_MODEL", "text-embedding-ada-002"
        )
        r = await openai.Embedding.acreate(
            deployment_id=AZURE_OPENAI_EMB_DEPLOYMENT,
            model=AZURE_OPENAI_EMB_MODEL,
            input=input,
        )
        return r["data"][0]["embedding"]  # type: ignore

    def __get_file_idxs_from_ids(
        self, category: CategoryCosmosDBModel, ids: List[str]
    ) -> List[int]:
        file_idxs = list(
            map(
                lambda id: next(
                    (i for i, file in enumerate(category.files) if file.id == id),
                ),
                ids,
            )
        )
        # This is necessary because each remove operation shifts back by one position
        if file_idxs:
            file_idxs.sort()
            for i, _ in enumerate(file_idxs):
                file_idxs[i] -= i
        return file_idxs

    async def put(
        self,
        category: CategoryModel,
        usecasetype_id: str,
        index_id: str,
        index_idx: int,
    ) -> List[CategoryCosmosDBModel]:
        current_cat_idx, current_cat = await self.__find_current_category(
            id=category.id, usecasetype_id=usecasetype_id, index_idx=index_idx
        )
        # 1. Step: Remove files:
        if category.filesToDelete:
            files_to_delete_ids = [file.id for file in category.filesToDelete]
            file_idxs = self.__get_file_idxs_from_ids(
                category=current_cat, ids=files_to_delete_ids
            )
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self.__delete_from_blob(files=files_to_delete_ids))
                tg.create_task(
                    self.__delete_files_from_db(
                        usecasetype_id=usecasetype_id,
                        index_idx=index_idx,
                        category_idx=current_cat_idx,
                        file_idxs=file_idxs,
                    )
                )
                for file_to_delete_id in files_to_delete_ids:
                    tg.create_task(
                        self.__delete_file_from_cog_search(file_id=file_to_delete_id)
                    )
        # 2. Step: upload new files
        if category.files:
            # check for new files
            file_ids = [file.id for file in category.files]
            current_file_ids = [file.id for file in current_cat.files]
            new_file_ids = list(
                set(file_ids) - set(current_file_ids)
            )  # set(a) & set(b) -> A n B; set(a) - set(b) -> A / B
            if new_file_ids:
                new_files = [file for file in category.files if file.id in new_file_ids]
                # TODO: Refactor. exactly the same code as post
                fr_service = FormRecognizerService()
                blob_service = BlobService()
                async with asyncio.TaskGroup() as tg:
                    blob_uploads: List[
                        asyncio.Task[Tuple[BlobClient, List[BlobClient]]]
                    ] = []
                    fr_analyzes: List[asyncio.Task[PREBUILTLAYOUT]] = []
                    file_ids: List[str] = []
                    file_names: List[str] = []
                    for file in new_files:
                        file_names.append(file.name)
                        if isinstance(file.data, str):
                            filemanagement_service = FileManagementService(
                                strategy=StrFileManagementStrategy()
                            )
                        else:
                            filemanagement_service = FileManagementService(
                                strategy=ByteFileManagementStrategy()
                            )
                        filesttart_instance = filemanagement_service.process_file(file)
                        file_ids.append(filesttart_instance.file_id)

                        files_for_blob_upload = filesttart_instance._to_model(
                            index_id, category.id
                        )
                        blob_upload: asyncio.Task[
                            Tuple[BlobClient, List[BlobClient]]
                        ] = tg.create_task(
                            blob_service.bulk_upload(
                                files_for_blob_upload, container=self._STORAGE_CONTAINER
                            )
                        )
                        fr_analyze: asyncio.Task[PREBUILTLAYOUT] = tg.create_task(
                            fr_service.analyze_document(
                                PREBUILTLAYOUT, filesttart_instance.file_bytes
                            )
                        )
                        blob_uploads.append(blob_upload)
                        fr_analyzes.append(fr_analyze)
                blob_upload_result = [
                    _blob_upload.result() for _blob_upload in blob_uploads
                ]
                fr_analyze_result = [
                    _fr_analyze.result() for _fr_analyze in fr_analyzes
                ]
                page_maps: List[List[Tuple[int, int, str]]] = [
                    FormRecognizerTextManagementService.convert_text(fr_analyze_result_)
                    for fr_analyze_result_ in fr_analyze_result
                ]
                files_as_sections: List[List[Tuple[str, int]]] = [
                    FormRecognizerTextManagementService.split_text(page_map)
                    for page_map in page_maps
                ]
                files_sections = await self.__create_cognitivesearch_document(
                    files_as_sections=files_as_sections,
                    file_names=file_names,
                    file_ids=file_ids,
                    category_id=category.id,
                )
                pages = [
                    [
                        PageCosmosDBModel(page_no=i, page_path=blob_page.url)
                        for i, blob_page in enumerate(blob_file_upload_result[1])
                    ]
                    for blob_file_upload_result in blob_upload_result
                ]
                files = [
                    FileCosmosDBModel(
                        id=file_id, name=file_name, path=blob_file[0].url, pages=page
                    )
                    for file_id, file_name, blob_file, page in list(
                        zip(file_ids, file_names, blob_upload_result, pages)
                    )
                ]
                patch_operation = [
                    {
                        "op": "add",
                        "path": f"/indices/{index_idx}/categories/{current_cat_idx}/files/-",
                        "value": file.jsonify(),
                    }
                    for file in files
                ]
                async with asyncio.TaskGroup() as tg:
                    tg.create_task(CognitiveSearchService().batch_index(files_sections))
                    tg.create_task(
                        CosmosDBService(
                            database=self._DATABASE, container=self._CONTAINER
                        ).batch_patch(
                            item_id=usecasetype_id,
                            partition_key=usecasetype_id,
                            patch_operations=patch_operation,
                        )
                    )
        # 3. Step: update fields:
        patch_operation = [
            {
                "op": "set",
                "path": f"/indices/{index_idx}/categories/{current_cat_idx}/name_de",
                "value": category.name_de,
            },
            {
                "op": "set",
                "path": f"/indices/{index_idx}/categories/{current_cat_idx}/name_en",
                "value": category.name_en,
            },
            {
                "op": "set",
                "path": f"/indices/{index_idx}/categories/{current_cat_idx}/description_de",
                "value": category.description_de,
            },
            {
                "op": "set",
                "path": f"/indices/{index_idx}/categories/{current_cat_idx}/description_en",
                "value": category.description_en,
            },
            {
                "op": "set",
                "path": f"/indices/{index_idx}/categories/{current_cat_idx}/system_prompt",
                "value": category.system_prompt,
            },
            {
                "op": "set",
                "path": f"/indices/{index_idx}/categories/{current_cat_idx}/temperature",
                "value": category.temperature,
            },
            {
                "op": "set",
                "path": f"/indices/{index_idx}/categories/{current_cat_idx}/model",
                "value": category.model,
            },
        ]
        patched_items = await self.__patch_db(
            usecasetype_id=usecasetype_id, patch=patch_operation
        )
        categories = [
            create_dataclass_from_dict(CategoryCosmosDBModel, item)
            for item in patched_items["indices"][index_idx]["categories"]
        ]
        return categories

    async def __create_cognitivesearch_document(
        self, files_as_sections, file_names, file_ids, category_id
    ):
        files_sections: List[Dict] = []
        for i, file_as_sections in enumerate(files_as_sections):
            file_sections: List[Dict] = []
            for content, page_num in file_as_sections:
                file_name = file_names[i]
                file_id = file_ids[i]
                embd: Union[List[float], None] = None
                if current_app.config["USE_EMBEDDINGS"]:
                    embd = await self.__create_embeddings(input=content)
                ctx = CognitiveSearchIndexStrategyProvider.get_context(
                    current_app.config["AZURE_SEARCH_INDEX"]
                )
                model = ctx.create_index_model(
                    id=f"{file_id}-page-{page_num}-{str(uuid.uuid1())}",
                    content=content,
                    category_id=category_id,
                    sourcepage=f"{os.path.splitext(os.path.basename(file_name))[0]}-{page_num}.pdf",
                    sourcefile=file_name,
                    embedding=embd,
                )
                single_section = model.jsonify()
                file_sections.append(single_section)
            files_sections.extend(file_sections)
        return files_sections

    async def post(
        self,
        category: CategoryModel,
        usecasetype_id: str,
        index_id: str,
        index_idx: int,
    ) -> List[CategoryCosmosDBModel]:
        fr_service = FormRecognizerService()
        blob_service = BlobService()
        async with asyncio.TaskGroup() as tg:
            blob_uploads: List[asyncio.Task[Tuple[BlobClient, List[BlobClient]]]] = []
            fr_analyzes: List[asyncio.Task[PREBUILTLAYOUT]] = []
            file_ids: List[str] = []
            file_names: List[str] = []
            for file in category.files:
                file_names.append(file.name)
                if isinstance(file.data, str):
                    filemanagement_service = FileManagementService(
                        StrFileManagementStrategy()
                    )
                else:
                    filemanagement_service = FileManagementService(
                        ByteFileManagementStrategy()
                    )
                filestrat_instance = filemanagement_service.process_file(file)
                file_ids.append(filestrat_instance.file_id)

                files_for_blob_upload = filestrat_instance._to_model(
                    index_id, category.id
                )
                blob_upload: asyncio.Task[
                    Tuple[BlobClient, List[BlobClient]]
                ] = tg.create_task(
                    blob_service.bulk_upload(
                        files_for_blob_upload, container=self._STORAGE_CONTAINER
                    )
                )
                fr_analyze: asyncio.Task[PREBUILTLAYOUT] = tg.create_task(
                    fr_service.analyze_document(
                        PREBUILTLAYOUT, filestrat_instance.file_bytes
                    )
                )
                blob_uploads.append(blob_upload)
                fr_analyzes.append(fr_analyze)
        blob_upload_result = [_blob_upload.result() for _blob_upload in blob_uploads]
        fr_analyze_result = [_fr_analyze.result() for _fr_analyze in fr_analyzes]
        page_maps: List[List[Tuple[int, int, str]]] = [
            FormRecognizerTextManagementService.convert_text(fr_analyze_result_)
            for fr_analyze_result_ in fr_analyze_result
        ]
        files_as_sections: List[List[Tuple[str, int]]] = [
            FormRecognizerTextManagementService.split_text(page_map)
            for page_map in page_maps
        ]

        files_sections = await self.__create_cognitivesearch_document(
            files_as_sections=files_as_sections,
            file_names=file_names,
            file_ids=file_ids,
            category_id=category.id,
        )

        pages = [
            [
                PageCosmosDBModel(page_no=i, page_path=blob_page.url)
                for i, blob_page in enumerate(blob_file_upload_result[1])
            ]
            for blob_file_upload_result in blob_upload_result
        ]
        files = [
            FileCosmosDBModel(
                id=file_id, name=file_name, path=blob_file[0].url, pages=page
            )
            for file_id, file_name, blob_file, page in list(
                zip(file_ids, file_names, blob_upload_result, pages)
            )
        ]
        category_model = CategoryCosmosDBModel(
            id=category.id,
            name_de=category.name_de,
            name_en=category.name_en,
            description_de=category.name_de,
            description_en=category.description_en,
            system_prompt=category.system_prompt,
            temperature=category.temperature,
            model=category.model,
            files=files,
        )
        patch_operation = [
            {
                "op": "add",
                "path": f"/indices/{index_idx}/categories/-",
                "value": category_model.jsonify(),
            }
        ]
        async with asyncio.TaskGroup() as tg:
            tg.create_task(CognitiveSearchService().batch_index(files_sections))
            patched_item = tg.create_task(
                CosmosDBService(
                    database=self._DATABASE, container=self._CONTAINER
                ).patch(
                    item_id=usecasetype_id,
                    partition_key=usecasetype_id,
                    patch=patch_operation,
                )
            )
        patched_items = patched_item.result()
        categories = [
            create_dataclass_from_dict(CategoryCosmosDBModel, item)
            for item in patched_items["indices"][index_idx]["categories"]
        ]
        return categories
