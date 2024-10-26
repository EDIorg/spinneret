"""The utilities module"""

from os import environ
from typing import Union
from urllib.parse import urlparse
from json import load
from lxml import etree
import pandas as pd


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


def is_url(text: str) -> bool:
    """
    :param text: The string to be checked.
    :returns: True if the string is likely a URL, False otherwise.
    :note: A string is considered a URL if it has scheme and network
        location values.
    """
    res = urlparse(text)
    if res.scheme != "" and res.netloc != "":
        return True
    return False


def load_workbook(
    workbook: Union[str, pd.core.frame.DataFrame]
) -> pd.core.frame.DataFrame:
    """
    :param workbook: The workbook to be loaded.
    :returns: The loaded workbook.
    """
    if isinstance(workbook, str):
        wb = pd.read_csv(workbook, sep="\t", encoding="utf-8", dtype=str)
    else:
        wb = workbook
    wb = wb.astype(str)  # dtype=str (above) not working for empty columns
    return wb


# pylint: disable=protected-access
def load_eml(eml: Union[str, etree._ElementTree]) -> etree._ElementTree:
    """
    :param eml: The EML file to be loaded.
    :returns: The loaded EML file.
    """
    if isinstance(eml, str):
        eml = etree.parse(eml, parser=etree.XMLParser(remove_blank_text=True))
    return eml
