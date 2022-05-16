# BLAB Chatbot - Watson Assistant

This Python module allows the integration of Watson Assistant chatbots with
BLAB.

### Installation

- Open a terminal window in the directory where
  [BLAB Controller](../../../blab-controller) is installed.
- Install this module in the same environment:

  ```shell
  poetry run python -m pip install git+https://github.com/C4AI/blab-chatbot-watson
  ```
- Open your controller settings file (`dev.py` or `prod.py`) and update
  the `CHAT_INSTALLED_BOTS` dictionary to include the Watson Assistant settings.
  Example with two chatbots using the same Watson account:

  ```python
  _watson_service_url = 'https://(...).assistant.watson.cloud.ibm.com/instances/(...)'
  _watson_api_key = '...'
  _watson_api_version = '...'
  _watson_dev_environment = True  # change to False in production
  
  # if it has not been defined yet, change it to CHAT_INSTALLED_BOTS = { ... }
  CHAT_INSTALLED_BOTS.update(
      {
          'Name of First Chatbot': (
              'blab_chatbot_watson.watson_assistant_bot',
              'WatsonAssistantBot',
              [],
              {
                  'service_url': _watson_service_url,
                  'api_key': _watson_api_key,
                  'api_version': _watson_api_version,
                  'assistant_id': '...',
                  'dev_environment': _watson_dev_environment,
              },
          ),
          'Name of Second Chatbot': (
              'blab_chatbot_watson.watson_assistant_bot',
              'WatsonAssistantBot',
              [],
              {
                  'service_url': _watson_service_url,
                  'api_key': _watson_api_key,
                  'api_version': _watson_api_version,
                  'assistant_id': '...',
                  'dev_environment': _watson_dev_environment,
              },
          ),
      }
  )
  ```
  Replace `...` with the appropriate values.

- Restart the controller.
