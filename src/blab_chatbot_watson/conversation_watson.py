"""A module that interacts with the APIs of Watson Assistant and BLAB Controller."""
from datetime import datetime
from typing import Any

from blab_chatbot_bot_client.conversation_websocket import (
    WebSocketBotClientConversation,
)
from blab_chatbot_bot_client.data_structures import (
    Message,
    MessageType,
    OutgoingMessage,
)
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson import AssistantV2
from ibm_watson.assistant_v2 import MessageInput
from overrides import overrides

from blab_chatbot_watson.watson_settings_format import BlabWatsonClientSettings


class WatsonWebSocketBotClientConversation(
    WebSocketBotClientConversation[BlabWatsonClientSettings]
):
    """Performs the communication between Watson Assistant and BLAB Controller."""

    def __init__(self, *args: Any, **kwargs: Any):
        """Create an instance."""
        super().__init__(*args, **kwargs)
        self.assistant = AssistantV2(
            version=self.settings.WATSON_SETTINGS["API_VERSION"],
            authenticator=IAMAuthenticator(self.settings.WATSON_SETTINGS["API_KEY"]),
        )
        self.assistant.set_service_url(self.settings.WATSON_SETTINGS["SERVICE_URL"])
        self.session_id = self._create_session()

    def _create_session(self) -> str:
        response = self.assistant.create_session(
            assistant_id=self.settings.WATSON_SETTINGS["ASSISTANT_ID"]
        ).get_result()
        return response["session_id"]

    @classmethod
    @overrides
    def bot_sends_first_message(cls) -> bool:
        return True

    @overrides
    def on_connect(self) -> None:
        for greeting in self.generate_greeting():
            self.enqueue_message(greeting)

    @overrides
    def generate_greeting(self) -> list[OutgoingMessage]:
        return self.generate_answer(
            Message(
                time=datetime.now(),
                text=" ",  # send empty message to Watson
                type=MessageType.TEXT,
                local_id=self.generate_local_id(),
                id="",
                sent_by_human=True,
            )
        )

    def send_message_to_watson(self, text: str) -> list[dict[str, Any]]:
        """Send a text message to the Watson bot (on behalf of the user).

        Args:
        ----
            text: the message text

        Returns:
        -------
            the list of raw messages returned by the bot
        """
        message_input = MessageInput(message_type="text", text=text)
        if self.settings.DEV_ENVIRONMENT:
            user_id = "DEVELOPMENT"
        else:
            user_id = "blab_conv_" + self.conversation_id

        response = self.assistant.message(
            assistant_id=self.settings.WATSON_SETTINGS["ASSISTANT_ID"],
            session_id=self.session_id,
            input=message_input,
            context=None,
            user_id=user_id,
        ).get_result()
        return response["output"]["generic"]

    @classmethod
    def process_bot_message(cls, message: dict[str, Any]) -> dict[str, Any]:
        """Process a message received from Watson bot.

        Args:
        ----
            message: the message as received from Watson

        Returns:
        -------
            a dictionary with the message that will be sent back to the user
        """

        def unify_text(title: str | None, description: str | None) -> str:
            if not description:
                return title or ""
            if not title:
                return description or ""
            return title + "\n\n" + description

        match (t := message["response_type"].lower()):
            case "text":
                return {"type": MessageType.TEXT, "text": message["text"]}

            case "option":
                return {
                    "type": MessageType.TEXT,
                    "text": message["title"],
                    "options": [o["label"] for o in message["options"]],
                }

            case "image" | "video" | "audio":
                return {
                    "type": {
                        "image": MessageType.IMAGE,
                        "video": MessageType.VIDEO,
                        "audio": MessageType.AUDIO,
                    }.get(t, MessageType.ATTACHMENT),
                    "external_file_url": message["source"],
                    "text": unify_text(
                        message.get("title", ""), message.get("description", "")
                    ),
                }

            case _:
                return {"type": MessageType.TEXT, "text": "UNSUPPORTED MESSAGE"}

    @overrides
    def on_receive_message(self, message: Message) -> None:
        if message.sent_by_human and message.type == MessageType.TEXT:
            for answer in self.generate_answer(message):
                self.enqueue_message(answer)

    @overrides
    def generate_answer(self, message: Message) -> list[OutgoingMessage]:
        if not message.text:
            return []
        return [
            OutgoingMessage(
                **self.process_bot_message(data),
                local_id=self.generate_local_id(),
                quoted_message_id=message.id or None,
            )
            for data in self.send_message_to_watson(message.text)
        ]
