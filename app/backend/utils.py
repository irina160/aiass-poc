from dataclasses import fields
from functools import wraps
import json
import traceback
from typing import (
    Any,
    Dict,
    List,
    Type,
)
import openai
from quart import request, current_app, jsonify
import requests
from jose import jwt
import os
import random
from azure.cosmos.aio import CosmosClient

from azure.search.documents.aio import SearchClient


from customerrors import (
    AuthError,
    NotInJsonFormatError,
    NotAValidPostRequest,
)

from schemas.BaseSchemas import BaseSchema


def require_auth(func):
    """Decorator for making sure user is authenticated. It uses quart.request context

    Args:
        func (_type_): Callable

    Raises:
        AuthError: Authorization error if token is not valid, token is not provided etc.

    Returns:
        _type_: Callable
    """

    @wraps(func)
    async def checkToken(*args, **kwargs):
        auth = request.authorization
        if not auth:
            raise AuthError(
                {
                    "code": "invalid header",
                    "description": "No Authorization Header provided",
                },
                401,
            )
        if auth.type != "bearer":
            raise AuthError(
                {
                    "code": "invalid header",
                    "description": "Wrong Authorization Method provided",
                },
                401,
            )
        if not auth.token:
            raise AuthError(
                {"code": "invalid header", "description": "No Token provided"}, 401
            )
        id_token = auth.token
        try:
            jwks = requests.get(
                "https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys".format(
                    tenant_id=os.getenv("AZURE_TENANT_ID_AUTH")
                )
            ).json()  # TODO: Replace AZURE_TENANT_ID_AUTH with AZURE_TENANT_ID if AAD in Sandbox is set up
            jwt_header = jwt.get_unverified_headers(id_token)
            rsa_key = {}
            for key in jwks["keys"]:
                if key["kid"] == jwt_header["kid"]:
                    rsa_key = {
                        "kty": key["kty"],
                        "kid": key["kid"],
                        "use": key["use"],
                        "n": key["n"],
                        "e": key["e"],
                    }
        except Exception:
            raise AuthError(
                {
                    "code": "invalid token",
                    "description": "Unable to parse authentication token",
                },
                401,
            )
        try:
            payload = jwt.decode(
                token=id_token,
                key=rsa_key,
                algorithms=["RS256"],
                audience=os.getenv("AZURE_CLIENT_ID_AUTH"),
                issuer="https://login.microsoftonline.com/{tenant_id}/v2.0".format(
                    tenant_id=os.getenv("AZURE_TENANT_ID_AUTH")
                ),
            )
        except Exception as exc:
            raise AuthError(
                {"code": "Not Authorized", "description": "Provided token is wrong"},
                401,
            )
        # TODO: Check if we need global/ user
        current_app.config["user"] = payload
        return await func(*args, **kwargs)

    return checkToken


def validate_json_request(schema: Type[BaseSchema]):
    def dec(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not request.is_json:
                raise NotInJsonFormatError(
                    {
                        "code": "should be in json format",
                        "description": f"Excepted application/json but got {request.mimetype}",
                    },
                    400,
                )
            req = await request.get_json()
            schema(**req)
            return await func(*args, **kwargs)

        return wrapper

    return dec


def require_json(f):
    """deprecated

    Args:
        f (_type_): _description_

    Raises:
        NotAValidPostRequest: _description_

    Returns:
        _type_: _description_
    """

    @wraps(f)
    async def dec(*args, **kwargs):
        if request.method == "POST":
            if not request.is_json:
                raise NotAValidPostRequest(
                    {
                        "code": "should be in json format",
                        "description": "Expected application/json, got {mimetype}".format(
                            mimetype=request.mimetype
                        ),
                    },
                    400,
                )
            else:
                return await f(*args, **kwargs)
        return await f(*args, **kwargs)

    return dec


def catch_and_return_http_code(f):
    @wraps(f)
    async def dec(*args, **kwargs):
        try:
            return await f(*args, **kwargs)
        except NotAValidPostRequest as e:
            return jsonify({"error": e.error}), e.status_code
        except AuthError as e:
            return jsonify({"error": e.error}), e.status_code
        except Exception as e:
            return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500

    return dec


async def query_items_from_db(
    client: CosmosClient,
    db_name: str,
    container_name: str,
    query: str,
    params: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    **Deprecated**
    queries items from the cosmosdb for nosql using the provided query

    Args:
        client (CosmosClient): instance of the client: CosmosClient(...)
        db_name (str): name of the db
        container_name (str): name of the container
        query (str): query of the form "Select * from Container c where c.name = @name"
        params (List[Dict[str, Any]]): Additional parameters in the form  [{"name": "@name", "value": "NAMEOFTHEITEM"}]

    Returns:
        List[Dict[str, Any]]: found items. If non are found [] is returned
    """
    db = client.get_database_client(db_name)
    container = db.get_container_client(container_name)
    arecords = container.query_items(query=query, parameters=params)
    records = [record async for record in arecords]
    return records


class ExampleQuestionsGenerator:
    NUMBER_OF_MAX_TOKENS: int = 200

    async def generate_example_questions(
        self,
        search_client: SearchClient,
        category_id: str,
        prompt: str,
        deployment: str,
        model: str,
    ):
        text = await self.query_sample_text(
            search_client=search_client, category_id=category_id
        )
        examples = await self.ask_openai(
            prompt=prompt, text=text, deployment=deployment, model=model
        )
        processed_examples = self.process_openai_answer(examples)
        return processed_examples

    async def ask_openai(self, prompt: str, text: str, deployment: str, model: str):
        p = prompt.format(text=text)
        chat_completion = await openai.ChatCompletion.acreate(
            deployment_id=deployment,
            model=model,
            messages=[{"role": "user", "content": p}],
            temperature=0.0,
            max_tokens=self.NUMBER_OF_MAX_TOKENS,
            n=1,
        )
        examples: str = chat_completion.choices[0].message.content
        return examples

    async def query_sample_text(self, search_client: SearchClient, category_id: str):
        ares = await search_client.search("", filter=f"category_id eq '{category_id}'")
        res = [r async for r in ares]
        lres = len(res)
        if lres:
            idx = random.randint(0, lres - 1)
            return res[idx]["content"]
        else:
            # TODO: make this (and the whole class) dynamic
            return """Generative AI can help increase productivity by quickly and accurately 
            answering questions and providing information, freeing up time for users to focus 
            on more important tasks. Businesses can take advantage of me by integrating me into 
            their workflows, automating certain tasks and processes, and leveraging my ability 
            to provide immediate assistance to users, leading to increased efficiency and cost 
            savings."""

    def process_openai_answer(self, examples: str) -> List[str]:
        # TODO: Make sure the examples is in json-structure (not any additional text)
        examples_json = json.loads(examples)
        return examples_json["questions_list"]


def create_dataclass_from_dict(dataclass_type: Type, data_dict: Dict):
    field_dict = {}
    for field in fields(dataclass_type):
        field_name = field.name
        field_type = field.type

        if field_name in data_dict:
            if hasattr(field_type, "__dataclass_fields__"):
                field_dict[field_name] = create_dataclass_from_dict(
                    field_type, data_dict[field_name]
                )
            elif isinstance(data_dict[field_name], list):
                if hasattr(field_type.__args__[0], "__dataclass_fields__"):
                    field_dict[field_name] = [
                        create_dataclass_from_dict(field_type.__args__[0], item)
                        for item in data_dict[field_name]
                    ]
            else:
                field_dict[field_name] = data_dict[field_name]
    return dataclass_type(**field_dict)
