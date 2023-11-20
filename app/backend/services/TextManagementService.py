from abc import ABC, abstractmethod
import html
from azure.ai.formrecognizer import DocumentTable
from typing import List, Tuple
from functools import singledispatchmethod
from services.FormRecognizerService import (
    PREBUILTDOCUMENT,
    PREBUILTLAYOUT,
    PREBUILTREAD,
)


class AbstractTextManagementService(ABC):
    ...


class TextManagementService(AbstractTextManagementService):
    ...


class AbstractFormRecognizerTextManagementService(AbstractTextManagementService):
    ...


class FormRecognizerTextManagementService(AbstractFormRecognizerTextManagementService):
    @staticmethod
    def table_to_html(table: DocumentTable) -> str:
        table_html = "<table>"
        rows = [
            sorted(
                [cell for cell in table.cells if cell.row_index == i],
                key=lambda cell: cell.column_index,
            )
            for i in range(table.row_count)
        ]
        for row_cells in rows:
            table_html += "<tr>"
            for cell in row_cells:
                tag = (
                    "th"
                    if (cell.kind == "columnHeader" or cell.kind == "rowHeader")
                    else "td"
                )
                cell_spans = ""
                if cell.column_span:
                    if cell.column_span > 1:
                        cell_spans += f" colSpan={cell.column_span}"
                if cell.row_span:
                    if cell.row_span > 1:
                        cell_spans += f" rowSpan={cell.row_span}"
                table_html += f"<{tag}{cell_spans}>{html.escape(cell.content)}</{tag}>"
            table_html += "</tr>"
        table_html += "</table>"
        return table_html

    @singledispatchmethod
    @staticmethod
    def convert_text(text):
        raise Exception("Use one of the provided FormRecognizerModelTypes")

    @convert_text.register
    @staticmethod
    def _(text: PREBUILTLAYOUT) -> List[Tuple[int, int, str]]:
        """
        This is still MSFT Code. We should double check if this is needed

        Args:
            text (PREBUILTLAYOUT): Text from AnalyzeResult

        Returns:
            _type_: _description_
        """
        offset = 0
        page_map: List[Tuple[int, int, str]] = []
        for page_num, page in enumerate(text.pages):
            # mark all positions of the table spans in the page
            page_offset = page.spans[0].offset
            page_length = page.spans[0].length

            page_text = ""
            added_tables = set()

            table_chars = [-1] * page_length
            if text.tables:
                tables_on_page = [
                    table
                    for table in text.tables
                    if table.bounding_regions[0].page_number == page_num + 1  # type: ignore
                ]

                for table_id, table in enumerate(tables_on_page):
                    for span in table.spans:
                        # replace all table spans with "table_id" in table_chars array
                        for i in range(span.length):
                            idx = span.offset - page_offset + i
                            if idx >= 0 and idx < page_length:
                                table_chars[idx] = table_id

            # build page text by replacing charcters in table spans with table html
            for idx, table_id in enumerate(table_chars):
                if table_id == -1:
                    page_text += text.content[page_offset + idx]
                elif table_id not in added_tables:
                    page_text += FormRecognizerTextManagementService.table_to_html(
                        tables_on_page[table_id]  # type: ignore
                    )
                    added_tables.add(table_id)

            page_text += " "
            page_map.append((page_num, offset, page_text))
            offset += len(page_text)
        return page_map

    @convert_text.register
    @staticmethod
    def _(text: PREBUILTDOCUMENT):
        raise NotImplementedError("Not yet implemeneted")

    @convert_text.register
    @staticmethod
    def _(text: PREBUILTREAD):
        raise NotImplementedError("Not yet implemeneted")

    @staticmethod
    def split_text(page_map: List[Tuple[int, int, str]]) -> List[Tuple[str, int]]:
        MAX_SECTION_LENGTH: int = 1000
        SENTENCE_SEARCH_LIMIT: int = 100
        SECTION_OVERLAP: int = 100
        SENTENCE_ENDINGS = [".", "!", "?"]
        WORDS_BREAKS = [",", ";", ":", " ", "(", ")", "[", "]", "{", "}", "\t", "\n"]

        def find_page(offset: int) -> int:
            num_pages = len(page_map)
            for i in range(num_pages - 1):
                if offset >= page_map[i][1] and offset < page_map[i + 1][1]:
                    return i
            return num_pages - 1

        all_text = "".join(p[2] for p in page_map)
        length = len(all_text)
        start: int = 0
        end = length
        res: List[Tuple[str, int]] = []
        while start + SECTION_OVERLAP < length:
            last_word = -1
            end = start + MAX_SECTION_LENGTH

            if end > length:
                end = length
            else:
                # Try to find the end of the sentence
                while (
                    end < length
                    and (end - start - MAX_SECTION_LENGTH) < SENTENCE_SEARCH_LIMIT
                    and all_text[end] not in SENTENCE_ENDINGS
                ):
                    if all_text[end] in WORDS_BREAKS:
                        last_word = end
                    end += 1
                if (
                    end < length
                    and all_text[end] not in SENTENCE_ENDINGS
                    and last_word > 0
                ):
                    end = last_word  # Fall back to at least keeping a whole word
            if end < length:
                end += 1

            # Try to find the start of the sentence or at least a whole word boundary
            last_word = -1
            while (
                start > 0
                and start > end - MAX_SECTION_LENGTH - 2 * SENTENCE_SEARCH_LIMIT
                and all_text[start] not in SENTENCE_ENDINGS
            ):
                if all_text[start] in WORDS_BREAKS:
                    last_word = start
                start -= 1
            if all_text[start] not in SENTENCE_ENDINGS and last_word > 0:
                start = last_word
            if start > 0:
                start += 1

            section_text = all_text[start:end]
            res.append((section_text, find_page(start)))

            last_table_start = section_text.rfind("<table")
            if (
                last_table_start > 2 * SENTENCE_SEARCH_LIMIT
                and last_table_start > section_text.rfind("</table")
            ):
                # If the section ends with an unclosed table, we need to start the next section with the table.
                # If table starts inside SENTENCE_SEARCH_LIMIT, we ignore it, as that will cause an infinite loop for tables longer than MAX_SECTION_LENGTH
                # If last table starts inside SECTION_OVERLAP, keep overlapping
                start = min(end - SECTION_OVERLAP, start + last_table_start)
            else:
                start = end - SECTION_OVERLAP

        if start + SECTION_OVERLAP < end:
            res.append((all_text[start:end], find_page(start)))
        return res
