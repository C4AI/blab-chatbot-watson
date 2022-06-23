"""This module is called from the command-line."""

import argparse
import sys
from configparser import ConfigParser
from pathlib import Path
from uuid import uuid4

from colorama import Style
from colorama import init as init_colorama

from blab_chatbot_watson.server import start_server
from blab_chatbot_watson.watson_assistant_bot import MessageType, WatsonAssistantBot

directory = Path(__file__).parent.parent.parent

parser = argparse.ArgumentParser()
parser.add_argument("--config", default=str(directory / "settings.ini"))
subparsers = parser.add_subparsers(help="command", dest="command")
index_parser = subparsers.add_parser("index", help="index document entries")
index_parser.add_argument(
    "--max-entries",
    type=int,
    default=sys.maxsize,
    help="maximum number of entries to index",
)
index_parser.add_argument(
    "--max-words", type=int, default=100, help="maximum number of words per entry"
)
serve_parser = subparsers.add_parser("startserver", help="start server")
answer_parser = subparsers.add_parser(
    "answer", help="answer question typed on terminal"
)
args = parser.parse_args()

p = Path(args.config)
if not p.is_file():
    print(f'Configuration file "{p}" not found.')
    sys.exit(1)
cp = ConfigParser()
cp.read(p)
config = cp["blab_chatbot_watson"]

service_url = config.get('service_url')
api_key = config.get('api_key')
api_version = config.get('api_version')
assistant_id = config.get('assistant_id')
dev_environment = config.getboolean('dev_environment', False)


init_colorama()

if args.command == "answer":

    def _new_id() -> str:
        return str(uuid4()).replace("-", "")

    bot = WatsonAssistantBot(
        service_url, api_key, api_version, assistant_id, dev_environment
    )
    conversation_id = 'DEVELOPMENT'
    bot.start_conversation(conversation_id)
    empty_message = {
        'type': MessageType.TEXT,
        'text': ' ',
        'id': _new_id(),
        'local_id': _new_id(),
        'sent_by_human': True,
    }
    answers = bot.answer(conversation_id, empty_message) or []
    while True:
        for answer in answers:
            print(
                Style.BRIGHT
                + "\n>> WATSON: "
                + Style.RESET_ALL
                + answer.get('text', '')
                + ' '
                + Style.DIM
                + ' / '.join(answer.get('options', []))
                + Style.RESET_ALL
            )

        try:
            question = input(Style.BRIGHT + "\n>> YOU: " + Style.RESET_ALL)
        except (EOFError, KeyboardInterrupt):
            question = ""
        if not question:
            break
        message = {
            'text': question,
            'type': MessageType.TEXT,
            'id': _new_id(),
            'sent_by_human': True,
        }
        answers = bot.answer(conversation_id, message) or []


elif args.command == "startserver":
    bot = WatsonAssistantBot(
        service_url, api_key, api_version, assistant_id, dev_environment
    )
    start_server(host=config["server_host"], port=config.getint("server_port"), bot=bot)
