"""This module allows the integration of Watson Assistant chatbots with BLAB."""
from typing import Any, Callable, Protocol

from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson import AssistantV2
from ibm_watson.assistant_v2 import MessageInput


class Message(Protocol):
    """Represents a Message (see Message on BLAB Controller's model)."""

    type: str
    text: str
    m_id: str

    def sent_by_human(self) -> bool:
        """Check if this message has been sent by a human user.

        Returns:
            True if and only if the message sender is human
        """
        pass


class ConversationInfo(Protocol):
    """Conversation interface available to bots."""

    conversation_id: str
    my_participant_id: str
    send_function: Callable[[dict[str, Any]], Message]


class MessageType:
    """Represents a message type."""

    SYSTEM = 'S'
    TEXT = 'T'
    VOICE = 'V'
    AUDIO = 'a'
    VIDEO = 'v'
    IMAGE = 'i'
    ATTACHMENT = 'A'


USER_ID = 'DEVELOPMENT'


class WatsonAssistantBot:
    """A bot provided by IBM Watson Assistant."""

    session_from_conversation_id = {}
    # TODO: save it on the database

    def __init__(
        self,
        conversation_info: ConversationInfo,
        *,
        service_url: str,
        api_key: str,
        api_version: str,
        assistant_id: str,
        dev_environment: bool = False,
    ):
        """
        .

        Args:
            conversation_info: an object that contains
                information about the conversation (see :cls:`ConversationInfo`)
            service_url: Watson service URL (shown on Watson website below the API key)
            api_key: Watson API key (shown on Watson website above service URL)
            api_version: Watson API version (see the official documentation
                `here <https://cloud.ibm.com/apidocs/assistant/assistant-v2>`_).
            assistant_id: id of the assistant (shown on Watson website after
                launching the chatbot, under "draft environment"/"live environment"
                - environment settings - API details).
            dev_environment: whether this is a development environment
        """
        self.conversation_info = conversation_info
        self.service_url = service_url
        self.api_key = api_key
        self.api_version = api_version
        self.assistant_id = assistant_id
        self.dev_environment = dev_environment

        self.assistant = AssistantV2(
            version=api_version, authenticator=IAMAuthenticator(api_key)
        )
        self.assistant.set_service_url(service_url)

        if (
            conversation_info.conversation_id
            not in WatsonAssistantBot.session_from_conversation_id
        ):
            WatsonAssistantBot.session_from_conversation_id[
                conversation_info.conversation_id
            ] = self._create_session()

    def _create_session(self) -> str:
        response = self.assistant.create_session(
            assistant_id=self.assistant_id
        ).get_result()
        return response['session_id']

    def receive_message(self, message: Message) -> None:
        """Receive a message from the user or other bots.

        Messages from other bots are ignored.

        Args:
            message: the received message
        """
        if not message.sent_by_human():
            return
        message_input = MessageInput(message_type='text', text=message.text)

        if self.dev_environment:
            user_id = 'DEVELOPMENT'
        else:
            user_id = 'blab_conv_' + str(self.conversation_info.conversation_id)

        response = self.assistant.message(
            assistant_id=self.assistant_id,
            session_id=WatsonAssistantBot.session_from_conversation_id[
                self.conversation_info.conversation_id
            ],
            input=message_input,
            context=None,
            user_id=user_id,
        ).get_result()
        answers = []
        for r in response['output']['generic']:
            answer = self.process_bot_message(r)
            answers.append(answer)
        if answers:
            answers[0]['quoted_message_id'] = str(message.m_id)
        for answer in answers:
            self.conversation_info.send_function(answer)

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
