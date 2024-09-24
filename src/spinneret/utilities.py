"""The utilities module"""

from os import environ
from urllib.parse import urlparse
from json import load
from lxml import etree


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


def delete_empty_tags(xml: etree._ElementTree) -> etree._ElementTree:
    """Deletes empty tags from an XML file

    :param xml: The XML file to be cleaned.
    :returns: The cleaned XML file.
    """
    for element in xml.xpath(".//*[not(node())]"):
        element.getparent().remove(element)
    return xml


def is_uri(text: str) -> bool:
    """
    :param text: The string to be checked.
    :returns: True if the string is likely a URI, False otherwise.
    :note: A string is considered a URI if it has scheme and network
        location values.
    """
    res = urlparse(text)
    if res.scheme != "" and res.netloc != "":
        return True
    return False
