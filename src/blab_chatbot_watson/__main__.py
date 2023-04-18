"""This module is called from the command-line."""

from sys import argv

from blab_chatbot_bot_client.cli import BlabBotClientArgParser

from blab_chatbot_watson.conversation_watson import WatsonWebSocketBotClientConversation

BlabBotClientArgParser(WatsonWebSocketBotClientConversation).parse_and_run(argv[1:])
