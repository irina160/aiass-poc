import argparse
import base64
import glob
import html
import io
import os
import re
import time

import openai
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azure.identity import AzureDeveloperCliCredential
from azure.cosmos import CosmosClient
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswParameters,
    PrioritizedFields,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SemanticConfiguration,
    SemanticField,
    SemanticSettings,
    SimpleField,
    VectorSearch,
    VectorSearchAlgorithmConfiguration,
)
from azure.storage.blob import BlobServiceClient
from pypdf import PdfReader, PdfWriter
from tenacity import retry, stop_after_attempt, wait_random_exponential

MAX_SECTION_LENGTH = 1000
SENTENCE_SEARCH_LIMIT = 100
SECTION_OVERLAP = 100

open_ai_token_cache = {}
CACHE_KEY_TOKEN_CRED = "openai_token_cred"
CACHE_KEY_CREATED_TIME = "created_time"
CACHE_KEY_TOKEN_TYPE = "token_type"

COSMOSDB_SERVICE = "cosmosdb120923"


def blob_name_from_file_page(filename, page=0):
    if os.path.splitext(filename)[1].lower() == ".pdf":
        return os.path.splitext(os.path.basename(filename))[0] + f"-{page}" + ".pdf"
    else:
        return os.path.basename(filename)


def upload_blobs(filename):
    blob_service = BlobServiceClient(
        account_url=f"https://{args.storageaccount}.blob.core.windows.net",
        credential=storage_creds,
    )
    blob_container = blob_service.get_container_client(args.container)
    if not blob_container.exists():
        blob_container.create_container()

    # if file is PDF split into pages and upload each page as a separate blob
    if os.path.splitext(filename)[1].lower() == ".pdf":
        reader = PdfReader(filename)
        pages = reader.pages
        for i in range(len(pages)):
            blob_name = blob_name_from_file_page(filename, i)
            if args.verbose:
                print(f"\tUploading blob for page {i} -> {blob_name}")
            f = io.BytesIO()
            writer = PdfWriter()
            writer.add_page(pages[i])
            writer.write(f)
            f.seek(0)
            blob_container.upload_blob(blob_name, f, overwrite=True)
    else:
        blob_name = blob_name_from_file_page(filename)
        with open(filename, "rb") as data:
            blob_container.upload_blob(blob_name, data, overwrite=True)


def remove_blobs(filename):
    if args.verbose:
        print(f"Removing blobs for '{filename or '<all>'}'")
    blob_service = BlobServiceClient(
        account_url=f"https://{args.storageaccount}.blob.core.windows.net",
        credential=storage_creds,
    )
    blob_container = blob_service.get_container_client(args.container)
    if blob_container.exists():
        if filename is None:
            blobs = blob_container.list_blob_names()
        else:
            prefix = os.path.splitext(os.path.basename(filename))[0]
            blobs = filter(
                lambda b: re.match(f"{prefix}-\d+\.pdf", b),
                blob_container.list_blob_names(
                    name_starts_with=os.path.splitext(os.path.basename(prefix))[0]
                ),
            )
        for b in blobs:
            if args.verbose:
                print(f"\tRemoving blob {b}")
            blob_container.delete_blob(b)


def table_to_html(table):
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
            if cell.column_span > 1:
                cell_spans += f" colSpan={cell.column_span}"
            if cell.row_span > 1:
                cell_spans += f" rowSpan={cell.row_span}"
            table_html += f"<{tag}{cell_spans}>{html.escape(cell.content)}</{tag}>"
        table_html += "</tr>"
    table_html += "</table>"
    return table_html


def get_document_text(filename):
    offset = 0
    page_map = []
    if args.localpdfparser:
        reader = PdfReader(filename)
        pages = reader.pages
        for page_num, p in enumerate(pages):
            page_text = p.extract_text()
            page_map.append((page_num, offset, page_text))
            offset += len(page_text)
    else:
        if args.verbose:
            print(f"Extracting text from '{filename}' using Azure Form Recognizer")
        form_recognizer_client = DocumentAnalysisClient(
            endpoint=f"https://{args.formrecognizerservice}.cognitiveservices.azure.com/",
            credential=formrecognizer_creds,
            headers={"x-ms-useragent": "azure-search-chat-demo/1.0.0"},
        )
        with open(filename, "rb") as f:
            poller = form_recognizer_client.begin_analyze_document(
                "prebuilt-layout", document=f
            )
        form_recognizer_results = poller.result()

        for page_num, page in enumerate(form_recognizer_results.pages):
            tables_on_page = [
                table
                for table in form_recognizer_results.tables
                if table.bounding_regions[0].page_number == page_num + 1
            ]

            # mark all positions of the table spans in the page
            page_offset = page.spans[0].offset
            page_length = page.spans[0].length
            table_chars = [-1] * page_length
            for table_id, table in enumerate(tables_on_page):
                for span in table.spans:
                    # replace all table spans with "table_id" in table_chars array
                    for i in range(span.length):
                        idx = span.offset - page_offset + i
                        if idx >= 0 and idx < page_length:
                            table_chars[idx] = table_id

            # build page text by replacing charcters in table spans with table html
            page_text = ""
            added_tables = set()
            for idx, table_id in enumerate(table_chars):
                if table_id == -1:
                    page_text += form_recognizer_results.content[page_offset + idx]
                elif table_id not in added_tables:
                    page_text += table_to_html(tables_on_page[table_id])
                    added_tables.add(table_id)

            page_text += " "
            page_map.append((page_num, offset, page_text))
            offset += len(page_text)

    return page_map


def split_text(page_map):
    SENTENCE_ENDINGS = [".", "!", "?"]
    WORDS_BREAKS = [",", ";", ":", " ", "(", ")", "[", "]", "{", "}", "\t", "\n"]
    if args.verbose:
        print(f"Splitting '{filename}' into sections")

    def find_page(offset):
        num_pages = len(page_map)
        for i in range(num_pages - 1):
            if offset >= page_map[i][1] and offset < page_map[i + 1][1]:
                return i
        return num_pages - 1

    all_text = "".join(p[2] for p in page_map)
    length = len(all_text)
    start = 0
    end = length
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
            if end < length and all_text[end] not in SENTENCE_ENDINGS and last_word > 0:
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
        yield (section_text, find_page(start))

        last_table_start = section_text.rfind("<table")
        if (
            last_table_start > 2 * SENTENCE_SEARCH_LIMIT
            and last_table_start > section_text.rfind("</table")
        ):
            # If the section ends with an unclosed table, we need to start the next section with the table.
            # If table starts inside SENTENCE_SEARCH_LIMIT, we ignore it, as that will cause an infinite loop for tables longer than MAX_SECTION_LENGTH
            # If last table starts inside SECTION_OVERLAP, keep overlapping
            if args.verbose:
                print(
                    f"Section ends with unclosed table, starting next section with the table at page {find_page(start)} offset {start} table start {last_table_start}"
                )
            start = min(end - SECTION_OVERLAP, start + last_table_start)
        else:
            start = end - SECTION_OVERLAP

    if start + SECTION_OVERLAP < end:
        yield (all_text[start:end], find_page(start))


def filename_to_id(filename):
    filename_ascii = re.sub("[^0-9a-zA-Z_-]", "_", filename)
    filename_hash = base64.b16encode(filename.encode("utf-8")).decode("ascii")
    return f"file-{filename_ascii}-{filename_hash}"


def create_sections(filename, page_map, use_vectors):
    file_id = filename_to_id(filename)
    for i, (content, pagenum) in enumerate(split_text(page_map)):
        section = {
            "id": f"{file_id}-page-{i}",
            "content": content,
            "category_id": args.category,
            "sourcepage": blob_name_from_file_page(filename, pagenum),
            "sourcefile": filename,
        }
        if use_vectors:
            section["embedding"] = compute_embedding(content)
        yield section


def before_retry_sleep(retry_state):
    if args.verbose:
        print("Rate limited on the OpenAI embeddings API, sleeping before retrying...")


@retry(
    wait=wait_random_exponential(min=1, max=60),
    stop=stop_after_attempt(15),
    before_sleep=before_retry_sleep,
)
def compute_embedding(text):
    refresh_openai_token()
    return openai.Embedding.create(engine=args.openaideployment, input=text)["data"][0][
        "embedding"
    ]


def create_search_index():
    if args.verbose:
        print(f"Ensuring search index {args.index} exists")
    index_client = SearchIndexClient(
        endpoint=f"https://{args.searchservice}.search.windows.net/",
        credential=search_creds,
    )
    if args.index not in index_client.list_index_names():
        index = SearchIndex(
            name=args.index,
            fields=[
                SimpleField(name="id", type="Edm.String", key=True),
                SearchableField(
                    name="content", type="Edm.String", analyzer_name="en.microsoft"
                ),
                SearchField(
                    name="embedding",
                    type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                    hidden=False,
                    searchable=True,
                    filterable=False,
                    sortable=False,
                    facetable=False,
                    vector_search_dimensions=1536,
                    vector_search_configuration="default",
                ),
                SimpleField(
                    name="category_id",
                    type="Edm.String",
                    filterable=True,
                    facetable=True,
                ),
                SimpleField(
                    name="sourcepage",
                    type="Edm.String",
                    filterable=True,
                    facetable=True,
                ),
                SearchableField(
                    name="sourcefile",
                    type="Edm.String",
                    filterable=True,
                    facetable=True,
                    analyzer_name="en.microsoft",
                ),
            ],
            semantic_settings=SemanticSettings(
                configurations=[
                    SemanticConfiguration(
                        name="default",
                        prioritized_fields=PrioritizedFields(
                            title_field=None,
                            prioritized_content_fields=[
                                SemanticField(field_name="content")
                            ],
                        ),
                    )
                ]
            ),
            vector_search=VectorSearch(
                algorithm_configurations=[
                    VectorSearchAlgorithmConfiguration(
                        name="default",
                        kind="hnsw",
                        hnsw_parameters=HnswParameters(metric="cosine"),
                    )
                ]
            ),
        )
        if args.verbose:
            print(f"Creating {args.index} search index")
        index_client.create_index(index)
    else:
        if args.verbose:
            print(f"Search index {args.index} already exists")


def index_sections(filename, sections):
    if args.verbose:
        print(f"Indexing sections from '{filename}' into search index '{args.index}'")
    search_client = SearchClient(
        endpoint=f"https://{args.searchservice}.search.windows.net/",
        index_name=args.index,
        credential=search_creds,
    )
    i = 0
    batch = []
    for s in sections:
        batch.append(s)
        i += 1
        if i % 1000 == 0:
            results = search_client.upload_documents(documents=batch)
            succeeded = sum([1 for r in results if r.succeeded])
            if args.verbose:
                print(f"\tIndexed {len(results)} sections, {succeeded} succeeded")
            batch = []

    if len(batch) > 0:
        results = search_client.upload_documents(documents=batch)
        succeeded = sum([1 for r in results if r.succeeded])
        if args.verbose:
            print(f"\tIndexed {len(results)} sections, {succeeded} succeeded")


def remove_from_index(filename):
    if args.verbose:
        print(
            f"Removing sections from '{filename or '<all>'}' from search index '{args.index}'"
        )
    search_client = SearchClient(
        endpoint=f"https://{args.searchservice}.search.windows.net/",
        index_name=args.index,
        credential=search_creds,
    )
    while True:
        filter = (
            None
            if filename is None
            else f"sourcefile eq '{os.path.basename(filename)}'"
        )
        r = search_client.search("", filter=filter, top=1000, include_total_count=True)
        if r.get_count() == 0:
            break
        r = search_client.delete_documents(documents=[{"id": d["id"]} for d in r])
        if args.verbose:
            print(f"\tRemoved {len(r)} sections from index")
        # It can take a few seconds for search results to reflect changes, so wait a bit
        time.sleep(2)


def setup_cosmosdb():
    cosmos_client = CosmosClient(
        url=f"https://{COSMOSDB_SERVICE}.documents.azure.com/", credential=cosmos_cred
    )
    demo_db = cosmos_client.get_database_client("Demo")
    keydata_db = cosmos_client.get_database_client("KeyData")
    useCaseDefinition_container = demo_db.get_container_client("UseCaseDefinition")
    useCaseDefinition_container.create_item(
        {
            "id": "7f1fd16d-4aef-11ee-ad31-3448ed340da2",
            "name_de": "Wissensmanagement",
            "name_en": "Knowledge Management",
            "description_de": "desc de",
            "description_en": "desc en",
            "indices": [],
        }
    )

    model_container = keydata_db.get_container_client("Model")
    model_container.create_item(
        {
            "id": "3972f45a-713d-4aaf-aa47-8c01b2e439eb",
            "display_name_de": "gpt-3.5-turbo",
            "display_name_en": "gpt-3.5-turbo",
            "model": "gpt-35-turbo",
        }
    )
    model_container.create_item(
        {
            "id": "6156d4c9-fc74-4c81-81a5-ce418b5389ed",
            "display_name_de": "gpt-4",
            "display_name_en": "gpt-4",
            "model": "gpt-4",
        }
    )
    model_container.create_item(
        {
            "id": "5ed9401c-33dd-4ab0-b386-7dc77bd24ca5",
            "display_name_de": "gpt-4-32k",
            "display_name_en": "gpt-4-32k",
            "model": "gpt-4-32k",
        }
    )

    prompts_container = keydata_db.get_container_client("Prompts")
    prompts_container.create_item(
        {
            "id": "98d97a44-4b38-4db1-849c-aadf81b6894a",
            "type": "followup",
            "content": 'Generate three very brief follow-up questions that the user would likely ask next. Use double angle brackets to reference the questions, e.g. <<Are there exclusions for prescriptions?>>. Try not to repeat questions that have already been asked. Only generate questions and do not generate any text before or after the questions, such as "Next Questions"',
        }
    )
    prompts_container.create_item(
        {
            "id": "3f1a0d9a-c456-4cc8-9abb-6b9b59f59750",
            "type": "query",
            "content": "Below is a history of the conversation so far, and a new question asked by the user that needs to be answered by searching in a knowledge base about employee healthcare plans and the employee handbook. Generate a search query based on the conversation and the new question. Do not include cited source filenames and document names e.g info.txt or doc.pdf in the search query terms. Do not include any text inside [] or <<>> in the search query terms. Do not include any special characters like '+'. If the question is not in English, translate the question to English before generating the search query. If you cannot generate a search query, return just the number 0.",
        }
    )
    prompts_container.create_item(
        {
            "id": "f5e252f5-2d39-4dc1-ba5d-1602f498221a",
            "type": "system",
            "content": "{category_system_prompt} \n Each source has a name followed by colon and the actual information, always include the source name for each fact you use in the response. Use square brackets to reference the source, e.g. [info1.txt]. Don't combine sources, list each source separately, e.g. [info1.txt][info2.pdf] {follow_up_questions_prompt} {injected_prompt}",
        }
    )
    prompts_container.create_item(
        {
            "id": "8d082b24-c8a6-4489-8b14-0161cff8f0e7",
            "type": "example",
            "content": "Create a python list containing three expert questions about the text delimited by triple backticks: ```{text}```. Format the response as json file containing this list under the entry 'questions_list'. The .json file entry should look like: 'questions_list':['question1', 'question2', 'question3']. Only provide the json, nothing more.",
        }
    )
    # fmt: off
    prompts_container.create_item(
        {
            "id": "8058089c-342a-474b-a73e-1e21d4034cd6",
            "type": "query_fewshots",
            # fmt: skip
            "content": "[{\"role\": \"user\", \"content\": \"What are my tax plans?\"}, {\"role\": \"assistant\", \"content\": \"Show available health plans\"}, {\"role\": \"user\", \"content\": \"does my plan cover cardio?\"}, {\"role\": \"assistant\", \"content\": \"Health plan cardio coverage\"}]"        }
    )
    # fmt: on

    temperature_container = keydata_db.get_container_client("Temperature")
    temperature_container.create_item(
        {
            "id": "e5210b44-1126-4c27-913f-978d60f1a6a4",
            "display_name_en": "precise",
            "display_name_de": "präzise",
            "temperature": 0,
        }
    )
    temperature_container.create_item(
        {
            "id": "06f27fdf-8f1c-45ac-b96f-669ed4e7ec71",
            "display_name_en": "balanced",
            "display_name_de": "ausbalanciert",
            "temperature": 0.5,
        }
    )
    temperature_container.create_item(
        {
            "id": "16257cfc-c071-42d7-8bd3-4249825287b7",
            "display_name_de": "kreativ",
            "display_name_en": "creative",
            "temperature": 1,
        }
    )


# refresh open ai token every 5 minutes
def refresh_openai_token():
    if (
        open_ai_token_cache[CACHE_KEY_TOKEN_TYPE] == "azure_ad"
        and open_ai_token_cache[CACHE_KEY_CREATED_TIME] + 300 < time.time()
    ):
        token_cred = open_ai_token_cache[CACHE_KEY_TOKEN_CRED]
        openai.api_key = token_cred.get_token(
            "https://cognitiveservices.azure.com/.default"
        ).token
        open_ai_token_cache[CACHE_KEY_CREATED_TIME] = time.time()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Prepare documents by extracting content from PDFs, splitting content into sections, uploading to blob storage, and indexing in a search index.",
        epilog="Example: prepdocs.py '..\data\*' --storageaccount myaccount --container mycontainer --searchservice mysearch --index myindex -v",
    )
    parser.add_argument("files", help="Files to be processed")
    parser.add_argument(
        "--category",
        help="Value for the category field in the search index for all sections indexed in this run",
    )
    parser.add_argument(
        "--skipblobs",
        action="store_true",
        help="Skip uploading individual pages to Azure Blob Storage",
    )
    parser.add_argument("--storageaccount", help="Azure Blob Storage account name")
    parser.add_argument("--container", help="Azure Blob Storage container name")
    parser.add_argument(
        "--storagekey",
        required=False,
        help="Optional. Use this Azure Blob Storage account key instead of the current user identity to login (use az login to set current user for Azure)",
    )
    parser.add_argument(
        "--tenantid",
        required=False,
        help="Optional. Use this to define the Azure directory where to authenticate)",
    )
    parser.add_argument(
        "--searchservice",
        help="Name of the Azure Cognitive Search service where content should be indexed (must exist already)",
    )
    parser.add_argument(
        "--index",
        help="Name of the Azure Cognitive Search index where content should be indexed (will be created if it doesn't exist)",
    )
    parser.add_argument(
        "--searchkey",
        required=False,
        help="Optional. Use this Azure Cognitive Search account key instead of the current user identity to login (use az login to set current user for Azure)",
    )
    parser.add_argument(
        "--openaiservice",
        help="Name of the Azure OpenAI service used to compute embeddings",
    )
    parser.add_argument(
        "--openaideployment",
        help="Name of the Azure OpenAI model deployment for an embedding model ('text-embedding-ada-002' recommended)",
    )
    parser.add_argument(
        "--novectors",
        action="store_true",
        help="Don't compute embeddings for the sections (e.g. don't call the OpenAI embeddings API during indexing)",
    )
    parser.add_argument(
        "--openaikey",
        required=False,
        help="Optional. Use this Azure OpenAI account key instead of the current user identity to login (use az login to set current user for Azure)",
    )
    parser.add_argument(
        "--remove",
        action="store_true",
        help="Remove references to this document from blob storage and the search index",
    )
    parser.add_argument(
        "--removeall",
        action="store_true",
        help="Remove all blobs from blob storage and documents from the search index",
    )
    parser.add_argument(
        "--localpdfparser",
        action="store_true",
        help="Use PyPdf local PDF parser (supports only digital PDFs) instead of Azure Form Recognizer service to extract text, tables and layout from the documents",
    )
    parser.add_argument(
        "--formrecognizerservice",
        required=False,
        help="Optional. Name of the Azure Form Recognizer service which will be used to extract text, tables and layout from the documents (must exist already)",
    )
    parser.add_argument(
        "--formrecognizerkey",
        required=False,
        help="Optional. Use this Azure Form Recognizer account key instead of the current user identity to login (use az login to set current user for Azure)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    # Use the current user identity to connect to Azure services unless a key is explicitly set for any of them
    azd_credential = (
        AzureDeveloperCliCredential()
        if args.tenantid is None
        else AzureDeveloperCliCredential(tenant_id=args.tenantid, process_timeout=60)
    )
    default_creds = (
        azd_credential if args.searchkey is None or args.storagekey is None else None
    )
    search_creds = (
        default_creds if args.searchkey is None else AzureKeyCredential(args.searchkey)
    )
    cosmos_cred = azd_credential
    use_vectors = not args.novectors

    if not args.skipblobs:
        storage_creds = default_creds if args.storagekey is None else args.storagekey
    if not args.localpdfparser:
        # check if Azure Form Recognizer credentials are provided
        if args.formrecognizerservice is None:
            print(
                "Error: Azure Form Recognizer service is not provided. Please provide formrecognizerservice or use --localpdfparser for local pypdf parser."
            )
            exit(1)
        formrecognizer_creds = (
            default_creds
            if args.formrecognizerkey is None
            else AzureKeyCredential(args.formrecognizerkey)
        )

    if use_vectors:
        if args.openaikey is None:
            openai.api_key = azd_credential.get_token(
                "https://cognitiveservices.azure.com/.default"
            ).token
            openai.api_type = "azure_ad"
            open_ai_token_cache[CACHE_KEY_CREATED_TIME] = time.time()
            open_ai_token_cache[CACHE_KEY_TOKEN_CRED] = azd_credential
            open_ai_token_cache[CACHE_KEY_TOKEN_TYPE] = "azure_ad"
        else:
            openai.api_type = "azure"
            openai.api_key = args.openaikey

        openai.api_base = f"https://{args.openaiservice}.openai.azure.com"
        openai.api_version = "2022-12-01"

    # setup_cosmosdb()

    if args.removeall:
        remove_blobs(None)
        remove_from_index(None)
    else:
        if not args.remove:
            create_search_index()

        print("Processing files...")
        for filename in glob.glob(args.files):
            if args.verbose:
                print(f"Processing '{filename}'")
            if args.remove:
                remove_blobs(filename)
                remove_from_index(filename)
            elif args.removeall:
                remove_blobs(None)
                remove_from_index(None)
            else:
                if not args.skipblobs:
                    upload_blobs(filename)
                page_map = get_document_text(filename)
                sections = create_sections(
                    os.path.basename(filename), page_map, use_vectors
                )
                index_sections(os.path.basename(filename), sections)
