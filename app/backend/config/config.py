from abc import ABC, abstractmethod
import os
from typing import Union
from azure.ai.formrecognizer.aio import DocumentAnalysisClient
from azure.identity import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential, AccessToken
from azure.search.documents.aio import SearchClient
from azure.storage.blob.aio import BlobServiceClient
from azure.cosmos.aio import CosmosClient
import openai

from approaches.retrievethenread import RetrieveThenReadApproach
from approaches.readretrieveread import ReadRetrieveReadApproach
from approaches.readdecomposeask import ReadDecomposeAsk
from approaches.chatreadretrieveread import ChatReadRetrieveReadApproach
from approaches.standardchat import StandardChatApproach

import configparser
import ast

config = configparser.ConfigParser()
config.read("config/settings.ini")


class AbstractConfigTemplate(ABC):
    @property
    @abstractmethod
    def AZURE_CREDENTIALS(self) -> Union[DefaultAzureCredential, None]:
        ...

    @property
    @abstractmethod
    def SEARCH_CLIENT(self) -> SearchClient:
        ...

    @property
    @abstractmethod
    def BLOB_CLIENT(self) -> BlobServiceClient:
        ...

    @property
    @abstractmethod
    def COSMOSDB_CLIENT(self) -> CosmosClient:
        ...

    @property
    @abstractmethod
    def FORMRECOGNIZER_CLIENT(self) -> DocumentAnalysisClient:
        ...

    @property
    @abstractmethod
    def OPENAI_TOKEN(self) -> AccessToken:
        ...


class Config(AbstractConfigTemplate):
    AZURE_SEARCH_SERVICE = os.getenv("AZURE_SEARCH_SERVICE", "gptkb")
    AZURE_SEARCH_SERVICE_KEY = os.getenv("AZURE_SEARCH_SERVICE_KEY", "")
    AZURE_OPENAI_SERVICE = os.getenv("AZURE_OPENAI_SERVICE", "myopenai")
    AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY", "")
    AZURE_OPENAI_CHATGPT_DEPLOYMENT = os.getenv(
        "AZURE_OPENAI_CHATGPT_DEPLOYMENT", "chat"
    )
    AZURE_OPENAI_CHATGPT_MODEL = os.getenv("AZURE_OPENAI_CHATGPT_MODEL", "gpt-35-turbo")
    AZURE_OPENAI_EMB_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMB_DEPLOYMENT", "embedding")
    AZURE_OPENAI_EMB_MODEL = os.getenv(
        "AZURE_OPENAI_EMB_MODEL", "text-embedding-ada-002"
    )
    AZURE_STORAGE_ACCOUNT = os.getenv("AZURE_STORAGE_ACCOUNT", "mystorageaccount")
    AZURE_STORAGE_CONTAINER = os.getenv("AZURE_STORAGE_CONTAINER", "content")
    AZURE_COSMOSDB_SERVICE = os.getenv("AZURE_COSMOSDB_SERVICE", "cosmosdb120923")
    AZURE_COSMOSDB_KEY = os.getenv("AZURE_COSMOSDB_KEY", "")
    AZURE_FORMRECOGNIZER_SERVICE = os.getenv(
        "AZURE_FORMRECOGNIZER_SERVICE", "formrecognizer-genai-1"
    )
    AZURE_FORMRECOGNIZER_KEY = os.getenv("AZURE_FORMRECOGNIZER_KEY", "")

    KB_FIELDS_CONTENT = os.getenv("KB_FIELDS_CONTENT", "content")
    KB_FIELDS_CATEGORY = os.getenv("KB_FIELDS_CATEGORY", "category")
    KB_FIELDS_SOURCEPAGE = os.getenv("KB_FIELDS_SOURCEPAGE", "sourcepage")

    @property
    def AZURE_SEARCH_INDEX(self):
        if ast.literal_eval(config["DEFAULT"]["USE_EMBEDDINGS"]):
            return config["cognitivesearch.index.embeddings"]["name"]
        else:
            return config["cognitivesearch.index.wo.embeddings"]["name"]

    @property
    def ASK_APPROACHES(self):
        return {
            "rtr": RetrieveThenReadApproach(
                self.SEARCH_CLIENT,
                self.AZURE_OPENAI_CHATGPT_DEPLOYMENT,
                self.AZURE_OPENAI_CHATGPT_MODEL,
                self.AZURE_OPENAI_EMB_DEPLOYMENT,
                self.KB_FIELDS_SOURCEPAGE,
                self.KB_FIELDS_CONTENT,
            )
        }

    @property
    def CHAT_APPROACHES(self):
        return {
            "rrr": ChatReadRetrieveReadApproach(
                self.SEARCH_CLIENT,
                self.AZURE_OPENAI_CHATGPT_DEPLOYMENT,
                self.AZURE_OPENAI_CHATGPT_MODEL,
                self.AZURE_OPENAI_EMB_DEPLOYMENT,
                self.KB_FIELDS_SOURCEPAGE,
                self.KB_FIELDS_CONTENT,
            ),
            "sc": StandardChatApproach(
                self.AZURE_OPENAI_CHATGPT_DEPLOYMENT, self.AZURE_OPENAI_CHATGPT_MODEL
            ),
        }

    def __init__(self):
        for key in config["DEFAULT"]:
            self.__setattr__(key.upper(), ast.literal_eval(config["DEFAULT"][key]))


class DevelopementConfig(Config):
    def __init__(self):
        openai.api_base = self.AZURE_OPENAI_SERVICE
        openai.api_version = "2023-05-15"
        openai.api_type = "azure"
        openai.api_key = self.OPENAI_TOKEN.token
        super().__init__()

    @property
    def AZURE_CREDENTIALS(self):
        return None

    @property
    def SEARCH_CLIENT(self):
        return SearchClient(
            endpoint=self.AZURE_SEARCH_SERVICE,
            index_name=self.AZURE_SEARCH_INDEX,
            credential=AzureKeyCredential(self.AZURE_SEARCH_SERVICE_KEY),
        )

    @property
    def BLOB_CLIENT(self):
        return BlobServiceClient.from_connection_string(self.AZURE_STORAGE_ACCOUNT)

    @property
    def COSMOSDB_CLIENT(self):
        return CosmosClient(
            self.AZURE_COSMOSDB_SERVICE, credential=self.AZURE_COSMOSDB_KEY
        )

    @property
    def FORMRECOGNIZER_CLIENT(self):
        return DocumentAnalysisClient(
            self.AZURE_FORMRECOGNIZER_SERVICE,
            credential=AzureKeyCredential(self.AZURE_FORMRECOGNIZER_KEY),
        )

    @property
    def OPENAI_TOKEN(self):
        return AccessToken(
            token=self.AZURE_OPENAI_KEY, expires_on=1725982316
        )  # expires never but for compatibility expires next year: 10.9.24


class ProductionConfig(Config):
    def __init__(self):
        openai.api_base = f"https://{self.AZURE_OPENAI_SERVICE}.openai.azure.com"
        openai.api_version = "2023-05-15"
        openai.api_type = "azure_ad"
        openai.api_key = self.OPENAI_TOKEN.token
        super().__init__()

    @property
    def AZURE_CREDENTIALS(self):
        return DefaultAzureCredential(exclude_shared_token_cache_credential=True)

    @property
    def FORMRECOGNIZER_CLIENT(self):
        return DocumentAnalysisClient(
            endpoint=f"https://{self.AZURE_FORMRECOGNIZER_SERVICE}.cognitiveservices.azure.com/",
            credential=self.AZURE_CREDENTIALS,  # type:ignore
        )

    @property
    def SEARCH_CLIENT(self):
        return SearchClient(
            endpoint=f"https://{self.AZURE_SEARCH_SERVICE}.search.windows.net",
            index_name=self.AZURE_SEARCH_INDEX,
            credential=self.AZURE_CREDENTIALS,  # type:ignore
        )

    @property
    def BLOB_CLIENT(self):
        return BlobServiceClient(
            account_url=f"https://{self.AZURE_STORAGE_ACCOUNT}.blob.core.windows.net",
            credential=self.AZURE_CREDENTIALS,
        )

    @property
    def COSMOSDB_CLIENT(self):
        return CosmosClient(
            url=f"https://{self.AZURE_COSMOSDB_SERVICE}.documents.azure.com",
            credential=self.AZURE_CREDENTIALS,  # type:ignore
        )

    @property
    def OPENAI_TOKEN(self):
        return self.AZURE_CREDENTIALS.get_token(
            "https://cognitiveservices.azure.com/.default"
        )
