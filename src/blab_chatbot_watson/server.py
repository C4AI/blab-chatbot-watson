"""HTTP server and WebSocket client used to interact with the controller."""

import json
import uuid
from threading import Thread

from flask import Flask, request
from websocket import WebSocketApp  # type: ignore

from blab_chatbot_watson.watson_assistant_bot import MessageType, WatsonAssistantBot

app = Flask(__name__)


@app.route("/", methods=["POST"])
def conversation_start() -> None:
    """Answer POST requests.

    This function will be called whenever there is a new conversation or
    an old connection is re-established.
    """
    # noinspection PyUnresolvedReferences
    bot: WatsonAssistantBot = app._BOT

    conversation_id = request.json["conversation_id"]

    def _new_id() -> str:
        return str(uuid.uuid4()).replace("-", "")

    def on_message(ws_app: WebSocketApp, m: str) -> None:
        """Send a message answering the question.

        This function is called when the WebSocket connection receives a message.

        Args:
            ws_app: the WebSocketApp instance
            m: message or event (JSON-encoded)
        """
        contents = json.loads(m)
        if "message" in contents:
            message = contents["message"]
            # ignore system messages and our own messages
            if not message.get("sent_by_human", False):
                return
            # generate answers
            answers = bot.answer(conversation_id, message) or []
            for i, answer in enumerate(answers):
                answer["local_id"] = _new_id()
                if i == 0:
                    answer["quoted_message_id"] = message["id"]
                # send answers
                Thread(target=lambda: ws_app.send(json.dumps(answer))).start()

    def on_open(ws_app: WebSocketApp) -> None:
        """Send an empty message to the server, so that it answers with a greeting message.

        This function is called when the WebSocket connection is opened.

        Args:
            ws_app: the WebSocketApp instance
        """
        bot.start_conversation(conversation_id)

        # empty message to start Watson Assistant bot
        fake_first_id = _new_id()
        empty_message = {
            'type': MessageType.TEXT,
            'text': ' ',
            'id': fake_first_id,
            'local_id': _new_id(),
            'sent_by_human': True,
        }

        def _answer_fn() -> None:
            answers = bot.answer(conversation_id, empty_message)
            for a in answers or []:
                if a.get('quoted_message_id', None) == fake_first_id:
                    del a['quoted_message_id']
                ws_app.send(json.dumps(a))

        Thread(target=_answer_fn).start()

    ws_url = "ws://localhost:8000/ws/chat/" + conversation_id + "/"
    ws = WebSocketApp(
        ws_url,
        on_message=on_message,
        cookie="sessionid=" + request.json["session"],
        on_open=on_open,
    )
    ws.conversation_id = request.json["conversation_id"]
    Thread(target=ws.run_forever).start()
    return ""


def start_server(host: str, port: int, bot: WatsonAssistantBot) -> None:
    """
    Start the HTTP server.

    Args:
        host:
            host to listen on (127.0.0.1 to accept only local connections,
            0.0.0.0 to accept all connections)
        port: port to listen on
        bot: Watson bot
    """
    app._BOT = bot
    app.run(host=host, port=port)
