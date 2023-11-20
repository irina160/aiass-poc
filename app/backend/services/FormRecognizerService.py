from typing import IO, TypeVar
from quart import current_app
from azure.ai.formrecognizer.aio import DocumentAnalysisClient
from azure.ai.formrecognizer import AnalyzeResult
from services.ABCAzureService import AbstractAzureService

CONFIG_FORMRECOGNIZER_CLIENT = "fr_client"

"""
See https://learn.microsoft.com/de-de/azure/ai-services/document-intelligence/concept-model-overview?view=doc-intel-3.1.0#model-data-extraction for a overview of supported
"""


class FormRecognizerModels(AnalyzeResult):
    _model: str = ""

    @classmethod
    def analyzeresult_to_model(cls, analyzeresult: AnalyzeResult):
        cls_obj = cls()
        for key, value in analyzeresult.__dict__.items():
            cls_obj.__dict__[key] = value
        return cls_obj


class PREBUILTLAYOUT(FormRecognizerModels):
    """
    Supported Extractions:
    - Text
    - Selection
    - Tables
    - New lines
    - Structure

    Args:
        AnalyzeResult (_type_): _description_
    """

    _model = "prebuilt-layout"


class PREBUILTDOCUMENT(FormRecognizerModels):
    """
    Supported Extractions:
    - Text
    - Selection
    - Tables
    - New lines
    - Key-Value-Pairs

    Args:
        AnalyzeResult (_type_): _description_
    """

    _model = "prebuilt-document"


class PREBUILTREAD(FormRecognizerModels):
    """
    Supported Extractions:
    - Text
    - Language
    - New lines

    Args:
        AnalyzeResult (_type_): _description_
    """

    _model = "prebuilt-read"


FormRecognizerModelTypes = TypeVar(
    "FormRecognizerModelTypes", bound=FormRecognizerModels
)


# It might be a good idea to also use begin_classify_document. This way we are able to use different models for extraction
class FormRecognizerService(AbstractAzureService):
    @property
    def client(self) -> DocumentAnalysisClient:
        return current_app.config[CONFIG_FORMRECOGNIZER_CLIENT]

    @client.setter
    def client(self):
        raise Exception("You are not allowed to set the client")

    async def analyze_document(
        self,
        model: type[FormRecognizerModelTypes],
        document: bytes | IO[bytes],
        **kwargs
    ) -> FormRecognizerModelTypes:
        poller = await self.client.begin_analyze_document(
            model._model, document, **kwargs
        )
        poller_result = await poller.result()
        casted_poller_result = model.analyzeresult_to_model(poller_result)
        # poller_result.__setattr__("model", model.model)
        # casted_poller_result = cast(model, poller_result)
        return casted_poller_result
