from typing import List
from pydantic import BaseModel
from quart import (
    Blueprint,
    Response,
    current_app,
    jsonify,
    request,
)
import json
import os
import aiohttp
import openai
from quart_schema import validate_headers, validate_response
from services.CosmosDBService import CosmosDBService
from services.ChatHistoryService import ChatHistoryService, ConversationModel
from customerrors import InternalServerError
from utils import (
    require_auth,
    require_json,
    catch_and_return_http_code,
    ExampleQuestionsGenerator,
)

from approaches.chatreadretrieveread import ChatReadRetrieveReadApproach
from approaches.standardchat import StandardChatApproach
from dataclasses import dataclass


AZURE_OPENAI_CHATGPT_DEPLOYMENT = os.getenv("AZURE_OPENAI_CHATGPT_DEPLOYMENT", "chat")
AZURE_OPENAI_CHATGPT_MODEL = os.getenv("AZURE_OPENAI_CHATGPT_MODEL", "gpt-35-turbo")

CONFIG_CHAT_APPROACHES = "chat_approaches"
CONFIG_COSMOSDB_CLIENT = "cosmosdb_client"
CONFIG_SEARCH_CLIENT = "search_client"
COSMOSDB_DATABASE_DEMO = "Demo"
COSMOSDB_CONTAINER_USECASEDEFINITION = "UseCaseDefinition"

COSMOSDB_DATABASE_KEYDATA = "KeyData"
COSMOSDB_CONTAINER_PROMPT = "Prompts"

chatBP = Blueprint(
    "chat",
    __name__,
    url_prefix="/api/usecasetypes/<usecasetype_id>/indices/<index_id>/categories/<category_id>",
)


@dataclass
class ConversationList:
    conversations: List[ConversationModel]


@chatBP.route(
    "/chat",
    methods=["GET"],
)
@catch_and_return_http_code
@require_auth
@validate_response(ConversationList, 200)
async def get_chat_histories(usecasetype_id, index_id, category_id) -> ConversationList:
    """_summary_"""
    chat_histories = await ChatHistoryService.get_all_histories(
        user_id=current_app.config["user"]["oid"],
        category_id=category_id,
    )
    return ConversationList(conversations=chat_histories)
    # return jsonify([asdict(chat_history) for chat_history in chat_histories])


@dataclass
class ExampleQuestions:
    example_questions: List[str]


@chatBP.route(
    "/chat/example_questions",
    methods=["GET"],
)
@catch_and_return_http_code
@require_auth
@validate_response(ExampleQuestions, 200)
async def get_example_questions(usecasetype_id, index_id, category_id):
    cdb_service = CosmosDBService(
        database=COSMOSDB_DATABASE_KEYDATA, container=COSMOSDB_CONTAINER_PROMPT
    )
    query = "Select p.type, p.content from Prompts p"
    prompts = await cdb_service.query(query=query)
    example_question_prompt = next(
        (prompt["content"] for prompt in prompts if prompt["type"] == "example")
    )
    async with aiohttp.ClientSession() as s:
        openai.aiosession.set(s)
        examples = await ExampleQuestionsGenerator().generate_example_questions(
            current_app.config[CONFIG_SEARCH_CLIENT],
            category_id,
            example_question_prompt,
            AZURE_OPENAI_CHATGPT_DEPLOYMENT,
            AZURE_OPENAI_CHATGPT_MODEL,
        )
    return ExampleQuestions(example_questions=examples)


@chatBP.route(
    "/chat/<chat_id>",
    methods=["GET"],
)
@catch_and_return_http_code
@require_auth
async def get_conversation(usecasetype_id, index_id, category_id, chat_id):
    user_id = current_app.config["user"]["oid"]
    conversation = await ChatHistoryService.get_conversation(
        user_id=user_id, category_id=category_id, conversation_id=chat_id
    )
    return jsonify(conversation), 200


@chatBP.route(
    "/chat/<chat_id>",
    methods=["POST"],
)
@catch_and_return_http_code
@require_auth
@require_json
async def collect_chat_query_and_answer(usecasetype_id, index_id, category_id, chat_id):
    request_json: dict = await request.get_json()
    conversation_new = request_json.get("new_conversation")
    chat = request_json
    approach: ChatReadRetrieveReadApproach | StandardChatApproach = current_app.config[
        CONFIG_CHAT_APPROACHES
    ].get(chat["approach"])

    cdb_service = CosmosDBService(
        database=COSMOSDB_DATABASE_DEMO, container=COSMOSDB_CONTAINER_USECASEDEFINITION
    )
    query = "Select u.indices from UseCaseDefinition u where u.id=@id"
    params = [{"name": "@id", "value": usecasetype_id}]
    items = await cdb_service.query(query=query, params=params)
    indices = items[0]["indices"]
    current_index = next((item for item in indices if item["id"] == index_id), None)

    current_category = next(
        (item for item in current_index["categories"] if item["id"] == category_id),
        None,
    )
    category_system_prompt = (
        current_category["system_prompt"]
        if len(current_category["system_prompt"])
        else None
    )

    cdb_service = CosmosDBService(
        database=COSMOSDB_DATABASE_KEYDATA, container=COSMOSDB_CONTAINER_PROMPT
    )
    query = "Select p.type, p.content from Prompts p"
    prompts = await cdb_service.query(query=query)
    followup_prompt = next(
        (prompt["content"] for prompt in prompts if prompt["type"] == "followup")
    )
    query_prompt = next(
        (prompt["content"] for prompt in prompts if prompt["type"] == "query")
    )
    system_prompt = next(
        (prompt["content"] for prompt in prompts if prompt["type"] == "system")
    )
    query_fewshots = next(
        (prompt["content"] for prompt in prompts if prompt["type"] == "query_fewshots")
    )

    try:
        async with aiohttp.ClientSession() as s:
            openai.aiosession.set(s)
            r = (
                await approach.run(
                    history=chat["history"],
                    overrides=chat["overrides"],
                    category_id=category_id,
                    system_prompt=system_prompt,
                    category_system_prompt=category_system_prompt,
                    query_prompt_template=query_prompt,
                    query_fewshots=json.loads(query_fewshots),
                    follow_up_question=followup_prompt,
                )
                or {}
            )
            await ChatHistoryService.add_to_history(
                user_id=current_app.config["user"]["oid"],
                category_id=category_id,
                conversation_id=chat_id,
                history=[chat["history"][-1], r],
            )
            if conversation_new:
                conversation_details = (
                    await ChatHistoryService.get_conversation_details(
                        user_id=current_app.config["user"]["oid"],
                        category_id=category_id,
                        conversation_id=chat_id,
                    )
                )
                r["conversation_details"] = conversation_details
                return jsonify(r)
            else:
                return jsonify(r)
    except Exception as e:
        raise InternalServerError(
            {
                "code": "Something went wrong",
                "description": f"We encountered an error: {e}",
            },
            500,
        )


@chatBP.route(
    "/chat/<chat_id>",
    methods=["DELETE"],
)
@catch_and_return_http_code
@require_auth
async def delete_chat_conversation(usecasetype_id, index_id, category_id, chat_id):
    user_id = current_app.config["user"]["oid"]
    await ChatHistoryService.delete_conversation(user_id, category_id, chat_id)
    return jsonify({"message": "success"}), 200
