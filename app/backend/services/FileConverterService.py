import io
import base64
from abc import ABC, abstractmethod


class AbstractFileConverterService(ABC):
    @abstractmethod
    def base64_to_bytes(self):
        ...

    @abstractmethod
    def base64_to_iobytes(self):
        ...


class FileConverterService(AbstractFileConverterService):
    @staticmethod
    def base64_to_bytes(base64_string: str) -> bytes:
        bytes_obj = base64.b64decode(base64_string.split(";base64,")[1])
        return bytes_obj

    @staticmethod
    def base64_to_iobytes(base64_string: str) -> io.BytesIO:
        bytes_obj = FileConverterService.base64_to_bytes(base64_string=base64_string)
        bytes_io_obj = io.BytesIO(bytes_obj)
        return bytes_io_obj

    @staticmethod
    def path_to_bytes(path: str) -> bytes:
        with open(path, "rb") as f:
            data = f.read()
        return data
