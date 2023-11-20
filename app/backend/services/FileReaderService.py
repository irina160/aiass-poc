import base64
from typing import List
from pypdf import PdfReader, PdfWriter
import io


class FileReaderService(PdfReader):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def pages_to_io(self) -> List[io.BytesIO]:
        pages: List[io.BytesIO] = []
        for i, page in enumerate(self.pages):
            f = io.BytesIO()
            writer = PdfWriter()
            writer.add_page(page)
            writer.write(f)
            f.seek(0)
            pages.append(f)
        return pages

    def pages_to_bytes(self) -> List[bytes]:
        pages = self.pages_to_io()
        return [page.getvalue() for page in pages]
