"""The utilities module"""

from os import environ
from json import load


def load_configuration(config_file: str) -> None:
    """Loads the configuration file as global environment variables for use
    by spinneret functions.

    :param config_file: The path to the configuration file.
    :returns: None
    :notes: Create a configuration file from `config.json.template` in the root
        directory of the project. Simply copy the template file and rename it
        to `config.json`. Fill in the values for the keys in the file.
    """
    with open(config_file, "r", encoding="utf-8") as config:
        config = load(config)
        for key, value in config.items():
            environ[key] = value
