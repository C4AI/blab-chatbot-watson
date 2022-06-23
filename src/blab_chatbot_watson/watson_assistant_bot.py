"""This module allows the integration of Watson Assistant chatbots with BLAB."""
from typing import Any

from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson import AssistantV2
from ibm_watson.assistant_v2 import MessageInput


class MessageType:
    """Represents a message type."""

    SYSTEM = 'S'
    TEXT = 'T'
    VOICE = 'V'
    AUDIO = 'a'
    VIDEO = 'v'
    IMAGE = 'i'
    ATTACHMENT = 'A'


class WatsonAssistantBot:
    """A bot provided by IBM Watson Assistant."""

    session_from_conversation_id = {}

    def __init__(
        self,
        service_url: str,
        api_key: str,
        api_version: str,
        assistant_id: str,
        dev_environment: bool = False,
    ):
        """
        .

        Args:
            service_url: Watson service URL (shown on Watson website below the API key)
            api_key: Watson API key (shown on Watson website above service URL)
            api_version: Watson API version (see the official documentation
                `here <https://cloud.ibm.com/apidocs/assistant/assistant-v2>`_).
            assistant_id: id of the assistant (shown on Watson website after
                launching the chatbot, under "draft environment"/"live environment"
                - environment settings - API details).
            dev_environment: whether this is a development environment
        """
        self.service_url = service_url
        self.api_key = api_key
        self.api_version = api_version
        self.assistant_id = assistant_id
        self.dev_environment = dev_environment
        self.assistant = AssistantV2(
            version=api_version, authenticator=IAMAuthenticator(api_key)
        )
        self.assistant.set_service_url(service_url)

    def _create_session(self) -> str:
        response = self.assistant.create_session(
            assistant_id=self.assistant_id
        ).get_result()
        return response['session_id']

    def start_conversation(self, conversation_id: str) -> None:
        """Start this conversation by creating a new Watson Assistant session.

        This method should be called before any calls to answer().

        Args:
            conversation_id: id of the conversation

        """
        if conversation_id not in WatsonAssistantBot.session_from_conversation_id:
            WatsonAssistantBot.session_from_conversation_id[
                conversation_id
            ] = self._create_session()

    def answer(
        self, conversation_id: str, message: dict[str, Any]
    ) -> list[dict[str, Any]] | None:
        """Receive a message from the user or other bots.

        Messages from other bots are ignored.

        Args:
            conversation_id: id of the conversation
            message: the received message
        """
        if not message.get("sent_by_human", False):
            return None
        text = message.get('text', None) or ''
        message_input = MessageInput(message_type='text', text=text)
        if message.get('type', None) != MessageType.TEXT:
            return [{'type': MessageType.TEXT, 'text': '?'}]
        if self.dev_environment:
            user_id = 'DEVELOPMENT'
        else:
            user_id = 'blab_conv_' + conversation_id

        response = self.assistant.message(
            assistant_id=self.assistant_id,
            session_id=WatsonAssistantBot.session_from_conversation_id[conversation_id],
            input=message_input,
            context=None,
            user_id=user_id,
        ).get_result()
        answers = []
        for r in response['output']['generic']:
            answers.append(self.process_bot_message(r))
        if answers:
            answers[0]['quoted_message_id'] = message['id']
        return answers

    @classmethod
    def process_bot_message(cls, message: dict[str, Any]) -> dict[str, Any]:
        """Process a message received from Watson bot.

        Args:
            message: the message as received from Watson

        Returns:
            a dictionary with the message that will be sent back to the user
        """

        def unify_text(title: str | None, description: str | None) -> str:
            if not description:
                return title
            if not title:
                return description
            return title + '\n\n' + description

        match (t := message['response_type'].lower()):
            case 'text':
                return {'type': MessageType.TEXT, 'text': message['text']}

            case 'option':
                return {
                    'type': MessageType.TEXT,
                    'text': message['title'],
                    'options': list(map(lambda o: o['label'], message['options'])),
                }

            case 'image' | 'video' | 'audio':
                return {
                    'type': {
                        'image': MessageType.IMAGE,
                        'video': MessageType.VIDEO,
                        'audio': MessageType.AUDIO,
                    }.get(t, MessageType.ATTACHMENT),
                    'external_file_url': message['source'],
                    'text': unify_text(
                        message.get('title', ''), message.get('description', '')
                    ),
                }

            case _:
                return {'type': MessageType.TEXT, 'text': "UNSUPPORTED MESSAGE"}
