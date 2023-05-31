"""A module that defines the expected format of the configuration file.

See the file ``settings_watson_TEMPLATE.py`` for a template.
"""

from typing import Protocol, TypedDict, runtime_checkable

from blab_chatbot_bot_client.settings_format import BlabWebSocketBotClientSettings


class WatsonSettings(TypedDict):
    """Contains parameters related to the IBM Watson Assistant service."""

    SERVICE_URL: str
    """Watson service URL"""

    API_KEY: str
    """Watson API key"""

    API_VERSION: str
    """Watson API version"""

    ASSISTANT_ID: str
    """Id of the Watson assistant"""


@runtime_checkable
class BlabWatsonClientSettings(BlabWebSocketBotClientSettings, Protocol):
    """A protocol that should be implemented by the configuration file.

    It extends the parent protocol (``BlabBotClientSettings``)
    with the inclusion of the ``WATSON_SETTINGS`` field.
    """

    WATSON_SETTINGS: WatsonSettings
    """Watson-specific settings"""

    DEV_ENVIRONMENT: bool
    """Whether the installation is in a development environment"""
