from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, NewType
import uuid
from customerrors import ConversationNotFoundError

from services.CosmosDBService import CosmosDBService
from utils import create_dataclass_from_dict


@dataclass
class ConversationModel:
    conversation_id: str
    timestamp: int
    topic: str


class ChatHistoryService:
    """
    For interacting with the ChatHistory.

    """

    _DATABASE = "User"
    _CONTAINER = "ChatHistory"

    @staticmethod
    def to_chat_history_model(items: List[Dict]) -> List[ConversationModel]:
        """Takes a list of dict-like chathistories and converts it to a ConversationModel

        Args:
            items (List[Dict]): list of chathistory items that contain conversation_id, timestamp and topic.

        Returns:
            List[ConversationModel]:

        Example:
            ```python
            chat_histories = [{"conversation_id": "123", "timestamp": 123456789, "topic": "distance from earth to sun"}]
            ChatHistoryService.to_chat_history_model(chat_histories)
            ```
        """
        items = [
            {
                "conversation_id": item["conversation_id"],
                "timestamp": item["timestamp"],
                "topic": item["topic"],
            }
            for item in items
        ]
        return [create_dataclass_from_dict(ConversationModel, item) for item in items]

    @staticmethod
    async def delete_chat_history_by_category(category_id: str):
        """Deletes a chathistory document from the cosmosdb by a given category_id (reference_id)

        Args:
            category_id (str): the category_id
        """
        cdb_service = CosmosDBService(
            ChatHistoryService._DATABASE, ChatHistoryService._CONTAINER
        )
        items = await cdb_service.query(
            query=f"Select * from {ChatHistoryService._CONTAINER} c where c.category_id = @category_id",
            params=[{"name": "@category_id", "value": category_id}],
        )
        item_ids = list(map(lambda item: item["id"], items))
        partition_keys = item_ids
        await cdb_service.bulk_delete(item_ids=item_ids, partition_keys=partition_keys)

    @staticmethod
    async def delete_conversation(user_id: str, category_id: str, conversation_id: str):
        """
        Deletes a conversation in a cosmosdb chathistory document. The documents are filtered by user_id, category_id and conversation_id.

        Args:
            user_id (str): id of the user
            category_id (str): id of the category
            conversation_id (str): id of the conversation to delete

        Raises:
            ConversationNotFoundError: Conversation could not be found
        """
        cdb_service = CosmosDBService(
            ChatHistoryService._DATABASE, ChatHistoryService._CONTAINER
        )
        items = await cdb_service.query(
            query=f"SELECT * from {ChatHistoryService._CONTAINER} c where c.userId = @user_id and c.category_id = @category_id",
            params=[
                {"name": "@user_id", "value": user_id},
                {"name": "@category_id", "value": category_id},
            ],
        )
        if not items or items is None:
            raise ConversationNotFoundError(
                f"Could not find conversation with id {conversation_id}"
            )
        item = items[0]
        item_id = item["id"]
        partition_key = item["id"]
        conversation_idx, conversation = next(
            (
                (i, itm)
                for i, itm in enumerate(item["histories"])
                if itm["conversation_id"] == conversation_id
            ),
            (None, None),
        )
        if conversation_idx is not None:
            await cdb_service.patch(
                item_id=item_id,
                partition_key=partition_key,
                patch=[{"op": "remove", "path": f"/histories/{conversation_idx}"}],
            )
        else:
            raise ConversationNotFoundError(
                f"Conversation with id {conversation_id} does not exist"
            )

    @staticmethod
    async def get_conversation(
        user_id: str, category_id: str, conversation_id: str
    ) -> Dict[str, Any]:
        """
        Returns a specific conversation from cosmosdb, filtered by user_id, category_id and conversation_id.

        Args:
            user_id (str): id of the user
            category_id (str): id of the category
            conversation_id (str): id of the conversation to get

        Returns:
            Dict[str, Any]: a chathistory conversation in the format
            ```python
                {
                    "history": [
                        {"user": "Some Question?"},
                        {
                            "answer": "Some Answer!",
                            "data_points": ["data_point1", ...],
                            "thoughts": "my thoughts"
                        }
                    ]
                }
            ```
        """
        cdb_service = CosmosDBService(
            ChatHistoryService._DATABASE, ChatHistoryService._CONTAINER
        )
        items = await cdb_service.query(
            query=f"SELECT t.history FROM {ChatHistoryService._CONTAINER} c JOIN t in c.histories where c.userId = @user_id and c.category_id = @category_id and t.conversation_id = @conversation_id ",
            params=[
                {"name": "@user_id", "value": user_id},
                {"name": "@category_id", "value": category_id},
                {"name": "@conversation_id", "value": conversation_id},
            ],
        )
        if not items or items is None:
            raise ConversationNotFoundError(
                f"Could not find conversation with id: {conversation_id}"
            )
        return items[0]

    @staticmethod
    async def get_conversation_details(
        user_id: str, category_id: str, conversation_id: str
    ) -> ConversationModel:
        """Gets the conversation details of a specific conversation from cosmosdb.

        Args:
            user_id (str): id of user
            category_id (str): id of category
            conversation_id (str): id of conversation to get

        Returns:
            ConversationModel:
        """
        cdb_service = CosmosDBService(
            ChatHistoryService._DATABASE, ChatHistoryService._CONTAINER
        )
        items = await cdb_service.query(
            query=f"SELECT t.conversation_id, t.topic, t.timestamp FROM {ChatHistoryService._CONTAINER} c JOIN t in c.histories where c.userId = @user_id and c.category_id = @category_id and t.conversation_id = @conversation_id ",
            params=[
                {"name": "@user_id", "value": user_id},
                {"name": "@category_id", "value": category_id},
                {"name": "@conversation_id", "value": conversation_id},
            ],
        )
        return ChatHistoryService.to_chat_history_model(items)[0]

    @staticmethod
    async def get_all_histories(
        user_id: str, category_id: str
    ) -> List[ConversationModel]:
        """Retrieves all chathistories from cosmosdb, filtered by user and category

        Args:
            user_id (str): id of the user
            category_id (str): id of the category

        Returns:
            List[ConversationModel]:
        """
        cdb_service = CosmosDBService(
            ChatHistoryService._DATABASE, ChatHistoryService._CONTAINER
        )
        items = await cdb_service.query(
            query=f"SELECT c.histories from {ChatHistoryService._CONTAINER} c where c.userId = @user_id and c.category_id = @category_id",
            params=[
                {"name": "@user_id", "value": user_id},
                {"name": "@category_id", "value": category_id},
            ],
        )
        if items:
            chat_history_models = ChatHistoryService.to_chat_history_model(
                items[0]["histories"]
            )
        else:
            chat_history_models = []
        return chat_history_models

    @staticmethod
    async def add_to_history(
        user_id: str, category_id: str, conversation_id: str, history: List[Dict]
    ) -> None:
        """Adds a history to a conversation.

        Args:
            user_id (str): user id
            category_id (str): category id
            conversation_id (str): conversation id
            history (List[Dict]): history in the format as given in the example. It might be different as well, based on the usecase but keep in mind that the frontend expects this kind of format

        Example:
            ```python
            history = [
                {
                    "user": "some question?"
                },
                {
                    "answer": "some answer",
                    "datapoints": ["datapoint1", ...],
                    "thoughts": "some thoughts"
                }
            ]
            ChatHistoryService.add_to_history(user_id, category_id, conversation_id, history)
            ```
        """
        item = await ChatHistoryService.get_user_history_document(
            user_id=user_id, category_id=category_id
        )
        if not item:
            item = await ChatHistoryService.create_new_user_history_document(
                user_id=user_id,
                category_id=category_id,
                conversation_id=conversation_id,
                history=history,
            )
            return
        item = item[0]
        id = item["id"]
        partition_key = item["id"]  # item["userId"]

        conversation_idx, conversation = next(
            (
                (i, itm)
                for i, itm in enumerate(item["histories"])
                if itm["conversation_id"] == conversation_id
            ),
            (None, None),
        )

        if conversation_idx is None:
            await ChatHistoryService.create_new_conversation(
                item_id=id,
                partition_key=partition_key,
                conversation_id=conversation_id,
                history=history,
            )
            return

        cdb_service = CosmosDBService(
            ChatHistoryService._DATABASE, ChatHistoryService._CONTAINER
        )
        item = await cdb_service.patch(
            item_id=id,
            partition_key=partition_key,
            patch=[
                {
                    "op": "add",
                    "path": f"/histories/{conversation_idx}/history/-",
                    "value": history_entry,
                }
                for history_entry in history
            ],
        )
        return

    @staticmethod
    async def get_user_history_document(
        user_id: str, category_id: str
    ) -> List[Dict[str, Any]]:
        """Gets all ChatHIstories from cosmosdb filtered by user_id and category_id

        Args:
            user_id (str): user id
            category_id (str): category id

        Returns:
            List[Dict[str, Any]]:
        """
        cdb_service = CosmosDBService(
            ChatHistoryService._DATABASE, ChatHistoryService._CONTAINER
        )
        item = await cdb_service.query(
            query=f"Select * from {ChatHistoryService._CONTAINER} c where c.userId = @user_id and c.category_id = @category_id",
            params=[
                {"name": "@user_id", "value": user_id},
                {"name": "@category_id", "value": category_id},
            ],
        )
        return item

    @staticmethod
    async def create_new_user_history_document(
        user_id: str, category_id: str, conversation_id: str, history: List[Dict]
    ) -> Dict:
        """Creates a new entry in a specific ChatHistory document in cosmosdb.

        Args:
            user_id (str): user id
            category_id (str): category id
            conversation_id (str): conversation id
            history (List[Dict]): history (same as in ChatHistoryService@add_to_history)

        Returns:
            Dict:
        """
        cdb_service = CosmosDBService(
            ChatHistoryService._DATABASE, ChatHistoryService._CONTAINER
        )
        new_item = await cdb_service.create_item(
            body={
                "id": str(uuid.uuid4()),
                "userId": user_id,
                "category_id": category_id,
                "histories": [
                    {
                        "conversation_id": conversation_id,
                        "topic": ChatHistoryService.generate_topic(
                            history
                        ),  # TODO: Replace with dynamically generated topic
                        "timestamp": int(datetime.now().timestamp()),
                        "history": history,
                    }
                ],
            }
        )
        return new_item

    @staticmethod
    async def create_new_conversation(
        item_id: str,
        partition_key: str,
        conversation_id: str,
        history: List[Dict],
    ) -> Dict[str, Any]:
        """Creates a new conversation in a specific ChatHistory document in cosmosdb

        Args:
            item_id (str): id of document in cosmosdb
            partition_key (str): partitionkey of document in cosmosdb
            conversation_id (str): conversation id
            history (List[Dict]): history (same as in ChatHistory@add_to_history)

        Returns:
            Dict[str, Any]:
        """
        cdb_service = CosmosDBService(
            ChatHistoryService._DATABASE, ChatHistoryService._CONTAINER
        )
        item = await cdb_service.patch(
            item_id=item_id,
            partition_key=partition_key,
            patch=[
                {
                    "op": "add",
                    "path": f"/histories/-",
                    "value": {
                        "conversation_id": conversation_id,
                        "topic": ChatHistoryService.generate_topic(
                            history
                        ),  # TODO: Replace with dynamically generated topic
                        "timestamp": int(datetime.now().timestamp()),
                        "history": history,
                    },
                }
            ],
        )
        return item

    @staticmethod
    def generate_topic(history: List[Dict]):
        return history[0]["user"]
