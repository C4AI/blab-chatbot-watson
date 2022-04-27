from typing import Any, Protocol, Callable

from ibm_watson import AssistantV2
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson.assistant_v2 import MessageInput


class Message(Protocol):
    """Represents a Message (see Message on BLAB Controller's model)"""

    type: str
    text: str
    m_id: str

    def sent_by_human(self) -> bool:
        pass


class ConversationInfo(Protocol):
    """Conversation interface available to bots."""

    conversation_id: str
    my_participant_id: str
    send_function: Callable[[dict[str, Any]], Message]


class MessageType:
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
    ):
        self.conversation_info = conversation_info
        self.service_url = service_url
        self.api_key = api_key
        self.api_version = api_version
        self.assistant_id = assistant_id

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
        if not message.sent_by_human():
            return
        message_input = MessageInput(message_type='text', text=message.text)

        response = self.assistant.message(
            assistant_id=self.assistant_id,
            session_id=WatsonAssistantBot.session_from_conversation_id[
                self.conversation_info.conversation_id
            ],
            input=message_input,
            context=None,
            user_id=USER_ID,
        ).get_result()
        answers = []
        for r in response['output']['generic']:
            answer = self.process_bot_message(r)
            answers.append(answer)
        if answers:
            answers[0]['quoted_message_id'] = str(message.m_id)
        for answer in answers:
            self.conversation_info.send_function(answer)

    def process_bot_message(self, message: dict[str, Any]) -> dict[str, Any]:
        def unify_text(title, description):
            if not description:
                return title
            if not title:
                return description
            return title + '\n\n' + description

        match (t := message['response_type'].lower()):
            case 'text':
                return {'type': MessageType.TEXT, 'text': message['text']}
            case 'option':
                # TODO: handle options in a better way
                return {
                    'type': MessageType.TEXT,
                    'text': message['title']
                    + '\n'
                    + ' / '.join(map(lambda o: o['label'], message['options'])),
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
                # TODO: implement other message types
                return {'type': MessageType.TEXT, 'text': "UNSUPPORTED MESSAGE"}
