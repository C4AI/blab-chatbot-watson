"""This module contains settings for Watson bot client."""

from blab_chatbot_bot_client.settings_format import BlabWebSocketConnectionSettings

from blab_chatbot_watson.watson_settings_format import WatsonSettings

# fmt: off

BLAB_CONNECTION_SETTINGS: BlabWebSocketConnectionSettings = {

    # Address of the (usually local) HTTP server that the controller will connect to:
    "BOT_HTTP_SERVER_HOSTNAME": "localhost",

    # Port of the aforementioned server:
    "BOT_HTTP_SERVER_PORT": 25227,

    # BLAB Controller address for WebSocket connections:
    "BLAB_CONTROLLER_WS_URL": "ws://localhost:8000",

}

WATSON_SETTINGS: WatsonSettings = {

    # Watson service URL (shown on Watson website below the API key):
    'SERVICE_URL': 'https://(...).assistant.watson.cloud.ibm.com/instances/(...)',

    # Watson API key (shown on Watson website above service URL):
    'API_KEY': '...',

    # Watson API version (see the official documentation
    # at <https://cloud.ibm.com/apidocs/assistant/assistant-v2>):
    'API_VERSION': '2021-11-27',

    # Id of the assistant (shown on Watson website after
    # launching the chatbot, under "draft environment"/"live environment" -
    # environment settings - API details):
    'ASSISTANT_ID': '...',
}

# whether this is a development environment:
DEV_ENVIRONMENT = True
