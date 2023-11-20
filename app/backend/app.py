import hashlib
import io
import logging
import mimetypes
import os
import time
from typing import Dict, List
import datetime

import aiohttp
import openai
from azure.core.credentials import AzureKeyCredential, AccessToken
from azure.ai.formrecognizer.aio import DocumentAnalysisClient
from azure.identity.aio import DefaultAzureCredential
from azure.monitor.opentelemetry import configure_azure_monitor
from azure.search.documents.aio import SearchClient
from azure.storage.blob.aio import BlobServiceClient
from azure.cosmos.aio import CosmosClient

from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware
from quart import (
    Blueprint,
    Quart,
    Response,
    abort,
    current_app,
    jsonify,
    request,
    send_file,
    send_from_directory,
)
from quart_schema import Contact, Info, QuartSchema, HttpSecurityScheme
from quart.views import MethodView

from approaches.chatreadretrieveread import ChatReadRetrieveReadApproach
from approaches.readdecomposeask import ReadDecomposeAsk
from approaches.readretrieveread import ReadRetrieveReadApproach
from approaches.retrievethenread import RetrieveThenReadApproach
from approaches.standardchat import StandardChatApproach

from utils import (
    require_auth,
    catch_and_return_http_code,
)

from chat import chatBP

from services.UsecaseTypeService import UsecaseTypeService
from services.IndexService import (
    IndexService,
)

from services.CategoryService import (
    CategoryService,
)

from models.Models import TemperatureModel, ModelModel

from providers.ModelProvider import ModelProvider, SupportedModelTypes

from config.config import DevelopementConfig, ProductionConfig

# Replace these with your own values, either in environment variables or directly here
# Search Vars
AZURE_SEARCH_SERVICE = os.getenv("AZURE_SEARCH_SERVICE", "gptkb")
AZURE_SEARCH_SERVICE_KEY = os.getenv("AZURE_SEARCH_SERVICE_KEY", "")
AZURE_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX", "gptkbindex")

# Openai Vars
AZURE_OPENAI_SERVICE = os.getenv("AZURE_OPENAI_SERVICE", "myopenai")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY", "")
## Remove this: does not exists anymore
AZURE_OPENAI_GPT_DEPLOYMENT = os.getenv("AZURE_OPENAI_GPT_DEPLOYMENT", "davinci")
##
AZURE_OPENAI_CHATGPT_DEPLOYMENT = os.getenv("AZURE_OPENAI_CHATGPT_DEPLOYMENT", "chat")
AZURE_OPENAI_CHATGPT_MODEL = os.getenv("AZURE_OPENAI_CHATGPT_MODEL", "gpt-35-turbo")
AZURE_OPENAI_EMB_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMB_DEPLOYMENT", "embedding")
AZURE_OPENAI_EMB_MODEL = os.getenv("AZURE_OPENAI_EMB_MODEL", "text-embedding-ada-002")
# Storage Vars
AZURE_STORAGE_ACCOUNT = os.getenv("AZURE_STORAGE_ACCOUNT", "mystorageaccount")
AZURE_STORAGE_CONTAINER = os.getenv("AZURE_STORAGE_CONTAINER", "content")

# Cosmosdb
AZURE_COSMOSDB_SERVICE = os.getenv("AZURE_COSMOSDB_SERVICE", "cosmosdb120923")
AZURE_COSMOSDB_KEY = os.getenv("AZURE_COSMOSDB_KEY", "")

# COSMOSDB
# FIXME: Hardcoded the database name - not really a good idea
# AZURE_COSMOSDB_SERVICE = os.environ.get("AZURE_COSMOSDB_ACCOUNT", "cosmosdb120923")
# Formrecognizer
AZURE_FORMRECOGNIZER_SERVICE = os.getenv(
    "AZURE_FORMRECOGNIZER_SERVICE", "formrecognizer-genai-1"
)
AZURE_FORMRECOGNIZER_KEY = os.getenv("AZURE_FORMRECOGNIZER_KEY", "")


KB_FIELDS_CONTENT = os.getenv("KB_FIELDS_CONTENT", "content")
KB_FIELDS_CATEGORY = os.getenv("KB_FIELDS_CATEGORY", "category")
KB_FIELDS_SOURCEPAGE = os.getenv("KB_FIELDS_SOURCEPAGE", "sourcepage")

CONFIG_OPENAI_TOKEN = "openai_token"
CONFIG_CREDENTIAL = "azure_credential"
CONFIG_ASK_APPROACHES = "ask_approaches"
CONFIG_CHAT_APPROACHES = "chat_approaches"
CONFIG_BLOB_CLIENT = "blob_client"
CONFIG_COSMOSDB_CLIENT = "cosmosdb_client"
CONFIG_FORMRECOGNIZER_CLIENT = "fr_client"
CONFIG_SEARCH_CLIENT = "search_client"
CONFIG_TEMPERATURE = "temperature_list"
CONFIG_MODEL = "model_list"

COSMOSDB_DATABASE_DEMO = "Demo"
COSMOSDB_CONTAINER_USECASEDEFINITION = "UseCaseDefinition"

COSMOSDB_DATABASE_KEYDATA = "KeyData"
COSMOSDB_CONTAINER_TEMPERATURE = "Temperature"
COSMOSDB_CONTAINER_MODEL = "Model"
COSMOSDB_CONTAINER_PROMPT = "Prompts"


APPLICATIONINSIGHTS_CONNECTION_STRING = os.getenv(
    "APPLICATIONINSIGHTS_CONNECTION_STRING"
)


bp = Blueprint("routes", __name__, static_folder="static")


@bp.route("/")
async def index():
    return await bp.send_static_file("index.html")


@bp.route("/<path:dummy>")
async def fallback(dummy):
    return await bp.send_static_file("index.html")


@bp.route("/favicon.ico")
async def favicon():
    return await bp.send_static_file("favicon.ico")


@bp.route("/assets/<path:path>")
async def assets(path):
    return await send_from_directory("static/assets", path)


class UsecaseTypeView(MethodView):
    @catch_and_return_http_code
    @require_auth
    async def get(self):
        service = UsecaseTypeService()
        usecasetypes = await service.get()

        temp: List[Dict[str, str]] = current_app.config[CONFIG_TEMPERATURE]
        model: List[Dict[str, str]] = current_app.config[CONFIG_MODEL]
        resp = {
            "usecasetypes": usecasetypes,
            "metadata": {"temperature": temp, "model": model},
        }
        return jsonify(resp), 200


class IndexView(MethodView):
    @catch_and_return_http_code
    @require_auth
    async def get(self, usecasetype_id):
        indices = await IndexService().get(usecasetype_id=usecasetype_id)
        return jsonify(indices), 200

    @catch_and_return_http_code
    @require_auth
    async def post(self, usecasetype_id):
        model = await ModelProvider().from_request(
            request=request, schema=SupportedModelTypes.Index
        )
        service = IndexService()
        new_indices = await service.post(index=model, usecasetype_id=usecasetype_id)

        return jsonify(new_indices), 201

    @catch_and_return_http_code
    @require_auth
    async def put(self, usecasetype_id):
        model = await ModelProvider().from_request(
            request=request, schema=SupportedModelTypes.Index
        )
        indices = await IndexService().put(index=model, usecasetype_id=usecasetype_id)
        return jsonify(indices), 200

    @catch_and_return_http_code
    @require_auth
    async def delete(self, usecasetype_id, index_id):
        indices = await IndexService().delete(index_id, usecasetype_id)
        return jsonify(indices), 200


"""
    We might use this for caching. This is just an example, so i will keep it here.
    Another approach would be to require a body in delete requests, such that the same api is used

    last_check = request.headers.get("If-Modified-Since")
    if last_check:
        last_check_as_date = datetime.datetime.strptime(
            last_check, "%a, %d %b %Y %H:%M:%S %Z"
        )
        try:
            last_change = current_app.config["Category_Last-Modified"]
        except KeyError:
            return "", 304
        last_change_as_date = datetime.datetime.strptime(
            last_change, "%a, %d %b %Y %H:%M:%S %Z"
        )
        if last_check_as_date > last_check_as_date:
            return "", 304

    For Delete (example):
    current_app.config["Category_Last-Modified"] = (
            datetime.datetime.now(datetime.timezone.utc)
            .strftime("%a, %d %b %Y %H:%M:%S %Z")
            .replace("UTC", "GMT")
        )
"""


class CategoryView(MethodView):
    @catch_and_return_http_code
    @require_auth
    async def get(self, usecasetype_id, index_id):
        categories = await CategoryService().get(
            usecasetype_id=usecasetype_id, index_id=index_id
        )
        return jsonify(categories), 200

    @catch_and_return_http_code
    @require_auth
    async def post(self, usecasetype_id, index_id):
        current_index_idx, _ = await IndexService().get_current_index_and_idx(
            id=index_id, usecasetype_id=usecasetype_id
        )
        model = await ModelProvider().from_request(
            request=request, schema=SupportedModelTypes.Category
        )
        category_service = CategoryService()
        categories = await category_service.post(
            category=model,
            usecasetype_id=usecasetype_id,
            index_id=index_id,
            index_idx=current_index_idx,
        )
        return jsonify(categories), 201

    @catch_and_return_http_code
    @require_auth
    async def put(self, usecasetype_id, index_id):
        current_index_idx, _ = await IndexService().get_current_index_and_idx(
            id=index_id, usecasetype_id=usecasetype_id
        )
        model = await ModelProvider().from_request(
            request=request, schema=SupportedModelTypes.Category
        )
        category_service = CategoryService()
        categories = await category_service.put(
            category=model,
            usecasetype_id=usecasetype_id,
            index_id=index_id,
            index_idx=current_index_idx,
        )
        return jsonify(categories), 201

    @catch_and_return_http_code
    @require_auth
    async def delete(self, usecasetype_id, index_id, category_id):
        (
            current_index_idx,
            current_index,
        ) = await IndexService().get_current_index_and_idx(
            id=index_id, usecasetype_id=usecasetype_id
        )
        categories = await CategoryService().delete(
            category_id, usecasetype_id=usecasetype_id, index_idx=current_index_idx
        )
        return jsonify(categories), 200


# Serve content files from blob storage from within the app to keep the example self-contained.
# *** NOTE *** this assumes that the content files are public, or at least that all users of the app
# can access all the files. This is also slow and memory hungry.


@bp.route(
    "/api/usecasetypes/<usecasetype_id>/indices/<index_id>/categories/<category_id>/chat/content/<path>"
)
@catch_and_return_http_code
async def content_file(usecasetype_id, index_id, category_id, path):
    blob_container = current_app.config[CONFIG_BLOB_CLIENT].get_container_client(
        AZURE_STORAGE_CONTAINER
    )
    blob = await blob_container.get_blob_client(
        f"{index_id}/{category_id}/pages/{path}"
    ).download_blob()
    if not blob.properties or not blob.properties.has_key("content_settings"):
        abort(404)
    mime_type = blob.properties["content_settings"]["content_type"]
    if mime_type == "application/octet-stream":
        mime_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
    blob_file = io.BytesIO()
    await blob.readinto(blob_file)
    blob_file.seek(0)
    return await send_file(
        blob_file, mimetype=mime_type, as_attachment=False, attachment_filename=path
    )


@bp.route("/api/ask", methods=["POST"])
async def ask():
    if not request.is_json:
        return jsonify({"error": "request must be json"}), 415
    request_json = await request.get_json()
    approach = request_json["approach"]
    try:
        impl = current_app.config[CONFIG_ASK_APPROACHES].get(approach)
        if not impl:
            return jsonify({"error": "unknown approach"}), 400
        # Workaround for: https://github.com/openai/openai-python/issues/371
        async with aiohttp.ClientSession() as s:
            openai.aiosession.set(s)
            r = await impl.run(
                request_json["question"], request_json.get("overrides") or {}
            )
        return jsonify(r)
    except Exception as e:
        logging.exception("Exception in /ask")
        return jsonify({"error": str(e)}), 500


@bp.after_request
async def set_headers(response: Response):
    if request.method in ["POST", "DELETE"]:
        response.headers.set("Cache-Control", "no-cache, no-store, must-revalidate")
        response.headers.set("Pragma", "no-cache")
        response.headers.set("Expires", "0")
    else:
        response.headers.set("Cache-Control", "max-age=3600")
        data = await response.get_data()
        response.headers.set("ETag", hashlib.sha1(data).hexdigest())
    response.headers.set(
        "Last-Modified",
        datetime.datetime.now(datetime.timezone.utc)
        .strftime("%a, %d %b %Y %H:%M:%S %Z")
        .replace("UTC", "GMT"),
    )
    response.headers.set("X-Content-Type-Options", "nosniff")
    response.headers.set("X-Frame-Options", "DENY")
    response.headers.set("Server", "hypercorn")
    response.headers.set("Referrer-Policy", "strict-origin-when-cross-origin")
    return response


@bp.before_request
async def ensure_openai_token():
    openai_token = current_app.config[CONFIG_OPENAI_TOKEN]
    if openai_token.expires_on < time.time() + 60:
        # this wont work in Dev mode but also not necessary since token does not expire
        openai_token = await current_app.config[CONFIG_CREDENTIAL].get_token(
            "https://cognitiveservices.azure.com/.default"
        )
        current_app.config[CONFIG_OPENAI_TOKEN] = openai_token
        openai.api_key = openai_token.token


@bp.before_app_serving
async def setup_clients():
    current_app.config["AZURE_SEARCH_INDEX"] = "gptkbindex-woe"
    current_app.config["USE_EMBEDDINGS"] = False
    if current_app.config["DEBUG"]:
        azure_credential = None
        search_client = SearchClient(
            endpoint=AZURE_SEARCH_SERVICE,
            index_name=current_app.config["AZURE_SEARCH_INDEX"],
            credential=AzureKeyCredential(AZURE_SEARCH_SERVICE_KEY),
        )
        blob_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_ACCOUNT)
        cosmosdb_client = CosmosClient(
            AZURE_COSMOSDB_SERVICE, credential=AZURE_COSMOSDB_KEY
        )
        formrecognizer_client = DocumentAnalysisClient(
            AZURE_FORMRECOGNIZER_SERVICE,
            credential=AzureKeyCredential(AZURE_FORMRECOGNIZER_KEY),
        )
        openai.api_base = AZURE_OPENAI_SERVICE
        openai.api_version = "2023-05-15"
        openai.api_type = "azure"
        openai_token = AccessToken(
            token=AZURE_OPENAI_KEY, expires_on=1725982316
        )  # expires never but for compatibility expires next year: 10.9.24
        openai.api_key = openai_token.token
    else:
        azure_credential = DefaultAzureCredential(
            exclude_shared_token_cache_credential=True
        )
        search_client = SearchClient(
            endpoint=f"https://{AZURE_SEARCH_SERVICE}.search.windows.net",
            index_name=current_app.config["AZURE_SEARCH_INDEX"],
            credential=azure_credential,
        )
        blob_client = BlobServiceClient(
            account_url=f"https://{AZURE_STORAGE_ACCOUNT}.blob.core.windows.net",
            credential=azure_credential,
        )
        cosmosdb_client = CosmosClient(
            url=f"https://{AZURE_COSMOSDB_SERVICE}.documents.azure.com",
            credential=azure_credential,
        )
        formrecognizer_client = DocumentAnalysisClient(
            endpoint=f"https://{AZURE_FORMRECOGNIZER_SERVICE}.cognitiveservices.azure.com/",
            credential=azure_credential,
        )
        # Used by the OpenAI SDK
        openai.api_base = f"https://{AZURE_OPENAI_SERVICE}.openai.azure.com"
        openai.api_version = "2023-05-15"
        openai.api_type = "azure_ad"
        openai_token = await azure_credential.get_token(
            "https://cognitiveservices.azure.com/.default"
        )
        openai.api_key = openai_token.token

    # Store on app.config for later use inside requests
    current_app.config[CONFIG_FORMRECOGNIZER_CLIENT] = formrecognizer_client
    current_app.config[CONFIG_SEARCH_CLIENT] = search_client
    current_app.config[CONFIG_OPENAI_TOKEN] = openai_token
    current_app.config[CONFIG_CREDENTIAL] = azure_credential
    current_app.config[CONFIG_BLOB_CLIENT] = blob_client
    current_app.config[CONFIG_COSMOSDB_CLIENT] = cosmosdb_client
    # Various approaches to integrate GPT and external knowledge, most applications will use a single one of these patterns
    # or some derivative, here we include several for exploration purposes
    current_app.config[CONFIG_ASK_APPROACHES] = {
        "rtr": RetrieveThenReadApproach(
            search_client,
            AZURE_OPENAI_CHATGPT_DEPLOYMENT,
            AZURE_OPENAI_CHATGPT_MODEL,
            AZURE_OPENAI_EMB_DEPLOYMENT,
            KB_FIELDS_SOURCEPAGE,
            KB_FIELDS_CONTENT,
        ),
        "rrr": ReadRetrieveReadApproach(
            search_client,
            AZURE_OPENAI_GPT_DEPLOYMENT,
            AZURE_OPENAI_EMB_DEPLOYMENT,
            KB_FIELDS_SOURCEPAGE,
            KB_FIELDS_CONTENT,
        ),
        "rda": ReadDecomposeAsk(
            search_client,
            AZURE_OPENAI_GPT_DEPLOYMENT,
            AZURE_OPENAI_EMB_DEPLOYMENT,
            KB_FIELDS_SOURCEPAGE,
            KB_FIELDS_CONTENT,
        ),
    }
    current_app.config[CONFIG_CHAT_APPROACHES] = {
        "rrr": ChatReadRetrieveReadApproach(
            search_client,
            AZURE_OPENAI_CHATGPT_DEPLOYMENT,
            AZURE_OPENAI_CHATGPT_MODEL,
            AZURE_OPENAI_EMB_DEPLOYMENT,
            KB_FIELDS_SOURCEPAGE,
            KB_FIELDS_CONTENT,
        ),
        "sc": StandardChatApproach(
            AZURE_OPENAI_CHATGPT_DEPLOYMENT, AZURE_OPENAI_CHATGPT_MODEL
        ),
    }

    keydata_db = cosmosdb_client.get_database_client(COSMOSDB_DATABASE_KEYDATA)
    temperature_container = keydata_db.get_container_client(
        COSMOSDB_CONTAINER_TEMPERATURE
    )
    atemperatures = temperature_container.query_items(
        query="SELECT t.id, t.display_name_de, t.display_name_en, t.temperature from t"
    )
    temperatures_ = [temp async for temp in atemperatures]
    temperatures = [
        TemperatureModel(**temp).retrieve_props_for_post() for temp in temperatures_
    ]
    current_app.config[CONFIG_TEMPERATURE] = temperatures

    model_container = keydata_db.get_container_client(COSMOSDB_CONTAINER_MODEL)
    amodels = model_container.query_items(
        query="SELECT m.id, m.display_name_de, m.display_name_en, m.model from m"
    )
    models_ = [model async for model in amodels]
    models = [ModelModel(**model).retrieve_props_for_post() for model in models_]
    current_app.config[CONFIG_MODEL] = models


@bp.after_app_serving
async def teardown_client():
    await current_app.config[CONFIG_COSMOSDB_CLIENT].close()


def create_app():
    if APPLICATIONINSIGHTS_CONNECTION_STRING:
        configure_azure_monitor()
        # AioHttpClientInstrumentor().instrument()
    app = Quart(__name__)
    QuartSchema(
        app,
        info=Info(
            title="Cognitive-Suite POC",
            version="0.1.0",
            contact=Contact(email="tutran1@kpmg.com", name="Tu Tran"),
            description="This is the API of the POC of the cognitivesuite GenAI Project. For feature or bug inquisitions please send an Email.",
        ),
        security_schemes={
            "bearerAuth": HttpSecurityScheme(
                type="http",
                description="Every Request has to be validated via a JWT token",
                scheme="bearer",
                bearer_format="JWT",
            )
        },
        security=[{"bearerAuth": []}],
    )

    bp.add_url_rule(
        "/api/usecasetypes",
        view_func=UsecaseTypeView.as_view("handle_usecase"),
    )
    bp.add_url_rule(
        "/api/usecasetypes/<usecasetype_id>/indices",
        methods=["GET", "POST", "PUT"],
        view_func=IndexView.as_view("handle_index"),
    )
    bp.add_url_rule(
        "/api/usecasetypes/<usecasetype_id>/indices/<index_id>",
        methods=["DELETE"],
        view_func=IndexView.as_view("handle_delete_index"),
    )
    bp.add_url_rule(
        "/api/usecasetypes/<usecasetype_id>/indices/<index_id>/categories",
        methods=["GET", "POST", "PUT"],
        view_func=CategoryView.as_view("handle_category"),
    )
    bp.add_url_rule(
        "/api/usecasetypes/<usecasetype_id>/indices/<index_id>/categories/<category_id>",
        methods=["DELETE"],
        view_func=CategoryView.as_view("handle_delete_category"),
    )
    bp.register_blueprint(chatBP)
    app.register_blueprint(bp)
    app.config["MAX_CONTENT_LENGTH"] = 40 * 1024 * 1024  # 40 MB
    app.asgi_app = OpenTelemetryMiddleware(app.asgi_app)
    return app
