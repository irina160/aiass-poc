import io
import os
from abc import ABC, abstractmethod
from typing import List, Union, TypeVar
import uuid
from models.Models import (
    PageBlobStorageModel,
    FileModel,
    FileBlobStorageModel,
)
from services.FileConverterService import FileConverterService
from services.FileReaderService import FileReaderService


# _T = TypeVar("_T", FileModel)


class FileManagementService:
    def __init__(self, strategy: "AbstractFileManagementStrategy"):
        self._strategy = strategy

    @property
    def strategy(self):
        return self._strategy

    @strategy.setter
    def strategy(self, strategy: "AbstractFileManagementStrategy"):
        self._strategy = strategy

    def process_file(self, file: FileModel) -> "AbstractFileManagementStrategy":
        strat = self._strategy.process_file(file)
        return strat

    def to_model(self, **kwargs) -> FileBlobStorageModel:
        return self._strategy._to_model(**kwargs)


class AbstractFileManagementStrategy(ABC):
    file_bytes: bytes
    file_name: str
    pages_bytes: List[bytes]
    page_names: List[str]

    def process_file(self, file: FileModel):
        """
        Template Method. Only transformation_to_bytes needs to be implemented in the subclasses.
        Otherwise this method processes the file and generates a file_model

        Args:
            file (_T): a file model
        """
        self.file = file
        self.generate_file_id()
        self.transform_to_bytes(file)
        self._bytes_to_io(self.file_bytes)
        self._get_pages_from_file(self.file_io)
        self._generate_names_for_pages(file.name, self.pages_bytes)
        return self

    @abstractmethod
    def transform_to_bytes(self, file: FileModel) -> bytes:
        ...

    def _to_model(
        self, index_id, category_id
    ) -> (
        FileBlobStorageModel
    ):  # probably move this method to another service / to another position or make it more generic
        return FileBlobStorageModel(
            data=self.file_bytes,
            path=f"{index_id}/{category_id}/{self.file.name}",
            tags={"id": self.file_id},
            pages=[
                PageBlobStorageModel(
                    data=page_data,
                    path=f"{index_id}/{category_id}/pages/{page_name}",
                    tags={"id": self.file_id},
                )
                for page_data, page_name in list(zip(self.pages_bytes, self.page_names))
            ],
        )

    def generate_file_id(self) -> str:
        self.file_id = str(uuid.uuid1())
        return self.file_id

    def _bytes_to_io(self, bytes_: bytes) -> io.BytesIO:
        self.file_io = io.BytesIO(bytes_)
        return self.file_io

    def _get_pages_from_file(self, stream: io.BytesIO) -> List[bytes]:
        filereader_service = FileReaderService(stream=stream)
        self.pages_bytes = filereader_service.pages_to_bytes()
        return self.pages_bytes

    def _generate_names_for_pages(
        self, name: str, pages: Union[List[bytes], int]
    ) -> List[str]:
        if type(pages) == int:
            iter_ = pages
        elif type(pages) == list:
            iter_ = len(pages)
        else:
            raise TypeError(
                f"Argument pages received an invalid argument type {type(pages)}"
            )
        pagenames: List[str] = []
        for i in range(iter_):
            pagename = os.path.splitext(name)[0] + f"-{i}" + ".pdf"
            pagenames.append(pagename)
        self.page_names = pagenames
        return pagenames


class ByteFileManagementStrategy(AbstractFileManagementStrategy):
    def transform_to_bytes(self, file: FileModel[bytes]) -> bytes:
        self.file_bytes = file.data
        return self.file_bytes


class StrFileManagementStrategy(AbstractFileManagementStrategy):
    def transform_to_bytes(self, file: FileModel[str]) -> bytes:
        if "base64" in file.data:
            self.file_bytes = FileConverterService.base64_to_bytes(file.data)
        else:
            self.file_bytes = FileConverterService.path_to_bytes(file.data)
        return self.file_bytes

    """
    def process_file(self, file: FileB64Model):
        self.generate_file_id()
        self._b64_to_bytes(file)
        self._bytes_to_io(file)
        self._get_pages_from_file()
        self._generate_names_for_pages(file.name, self.pages_bytes)

    def _get_pages_from_file(self, file) -> List[bytes]:
        filereader_service = FileReaderService(stream=self.file_io)
        self.pages_bytes = filereader_service.pages_to_bytes()
        return self.pages_bytes
    """

    """
    def process_b64_file(self):
        io_bytes_obj = self._b64_to_io(self.file)
        self._b64_to_bytes(self.file)
        pages_io = self._get_pages_from_file_io(io_bytes_obj)
        pagenames = self._generate_names_for_pages(self.file.name, pages_io)

    def to_model(
        self, index_id, category_id
    ) -> (
        FileBlobUploadModel
    ):  # probably move this method to another service / to another position or make it more generic
        return FileBlobUploadModel(
            data=self.file_bytes,
            path=f"{index_id}/{category_id}/{self.file.name}",
            tags={"id": self.file_id},
            pages=[
                PageBlobUploadModel(
                    data=page_data,
                    path=f"{index_id}/{category_id}/pages/{page_name}",
                    tags={"id": self.file_id},
                )
                for page_data, page_name in list(zip(self.pages_io, self.page_names))
            ],
        )

    def generate_file_id(self) -> str:
        self.file_id = str(uuid.uuid1())
        return self.file_id
    """

    """
    def _generate_names_for_pages(
        self, name: str, pages: Union[List[bytes], int]
    ) -> List[str]:
        if type(pages) == int:
            iter_ = pages
        elif type(pages) == list:
            iter_ = len(pages)
        else:
            raise TypeError(
                f"Argument pages received an invalid argument type {type(pages)}"
            )
        pagenames: List[str] = []
        for i in range(iter_):
            pagename = os.path.splitext(name)[0] + f"-{i}" + ".pdf"
            pagenames.append(pagename)
        self.page_names = pagenames
        return pagenames

    def _b64_to_bytes(self, file: FileB64Model) -> bytes:
        self.file_bytes = FileConverterService.base64_to_byte(file.data)
        return self.file_bytes

    def _b64_to_io(self, file: FileB64Model) -> io.BytesIO:
        self.file_io = FileConverterService.base64_to_iobyte(file.data)
        return self.file_io
    """

    """
    def _get_pages_from_file_io(self, stream: io.BytesIO) -> List[io.BytesIO]:
        file_reader = FileReaderService(stream=stream)
        self.pages_io = file_reader.pages_to_io()
        return self.pages_io
    """
