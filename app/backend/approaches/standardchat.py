from typing import Any, List

import openai
from approaches.chatreadretrieveread import ChatReadRetrieveReadApproach
from core.modelhelper import get_token_limit


class StandardChatApproach(ChatReadRetrieveReadApproach):
    def __init__(
        self,
        chatgpt_deployment: str,
        chatgpt_model: str,
    ):
        self.chatgpt_deployment = chatgpt_deployment
        self.chatgpt_model = chatgpt_model
        self.chatgpt_token_limit = get_token_limit(chatgpt_model)

    async def run(
        self,
        history: List[dict[str, str]],
        overrides: dict[str, Any],
        category_system_prompt: str | None = None,
        follow_up_question: str | None = None,
        *args,
        **kwargs,
    ) -> Any:
        messages = self.get_messages_from_history(
            category_system_prompt or "",
            self.chatgpt_model,
            history,
            # Model does not handle lengthy system messages well. Moving sources to latest user conversation to solve follow up questions prompt.
            history[-1]["user"],
            max_tokens=self.chatgpt_token_limit - 1024,
        )

        chat_completion = await openai.ChatCompletion.acreate(
            deployment_id=self.chatgpt_deployment,
            model=self.chatgpt_model,
            messages=messages,
            temperature=overrides.get("temperature") or 0.7,
            max_tokens=1024,
            n=1,
        )

        chat_content = chat_completion.choices[0].message.content

        msg_to_display = "\n\n".join([str(message) for message in messages])

        return {
            "data_points": [],
            "answer": chat_content,
            "thoughts": f"Searched for:<br>{history[-1]['user']}<br><br>Conversations:<br>"
            + msg_to_display.replace("\n", "<br>"),
        }
