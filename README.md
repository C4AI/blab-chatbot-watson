# BLAB Chatbot - Watson Assistant

This Python module allows the integration of Watson Assistant chatbots with
BLAB.

### Installation

- Clone or download this repository.
- In the directory that contains this *README.md* file,
  create a file *settings.ini* with the following contents and fill in the blanks:

  ```ini
  [blab_chatbot_watson]
  service_url=https://(...).assistant.watson.cloud.ibm.com/instances/(...)
  api_key=...
  api_version=...
  assistant_id=...
  dev_environment=...
  server_host=127.0.0.1
  server_port=25227
  ws_url=...
  ```

  The field `dev_environment` should be set to _True_ in develompent environments
  and _False_ in production. The field `ws_url` must be the controller address
  (e.g. _ws://localhost:8000_ in a development installation). The server host should be `server_host` should be *127.0.0.1* to accept only local connections from
  the controller, and the port is arbitrary.

- Install
[Python 3.10](https://www.python.org/downloads/release/python-3100/)
or newer.

- Install [Poetry](https://python-poetry.org/) (version 1.2 or newer):

  ```shell
  curl -sSL https://install.python-poetry.org | python3 - --preview
  ```
  If *~/.local/bin* is not in `PATH`, add it as suggested by the output of Poetry installer.

- Run Poetry to install the dependencies in a new virtual environment (_.venv_):

  ```shell
  POETRY_VIRTUALENVS_IN_PROJECT=true poetry install
  ```

- Optionally, run `poetry shell` to open a shell that uses the virtual environment, and
  all the commands below can be executed on that shell without prefixing them with `poetry run`.

- To open an interactive demo that answers questions, run:

  ```shell
  poetry run python run.py answer
  ```

- In order to start the server that will interact with BLAB Controller, run:

  ```shell
  poetry run python run.py startserver
  ```


- Open your controller settings file (`dev.py` or `prod.py`) and update
  the `CHAT_INSTALLED_BOTS` dictionary to include the Watson Assistant settings.
  Example:

  ```python
  # if it has not been defined yet, change it to CHAT_INSTALLED_BOTS = { ... }
  CHAT_INSTALLED_BOTS.update(
      {
          'Chatbot Name Using Watson': (
              'chat.bots',
              'WebSocketExternalBot',
              ['http://localhost:25227/'],
              {},
          ),
      }
  )
  ```

- Restart the controller.
