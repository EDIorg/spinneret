"""The utilities module"""

from os import environ
from typing import Union
from urllib.parse import urlparse
from json import load

from prefixmaps import load_converter
from curies import Converter
import pandas as pd
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
    wb.fillna(pd.NA, inplace=True)
    return wb


# pylint: disable=protected-access
def load_eml(eml: Union[str, etree._ElementTree]) -> etree._ElementTree:
    """
    :param eml: The EML file to be loaded.
    :returns: The loaded EML file.
    """
    if isinstance(eml, str):
        eml = etree.parse(eml, parser=etree.XMLParser(remove_blank_text=True))
    eml = delete_empty_tags(eml)
    return eml


def write_workbook(workbook: pd.core.frame.DataFrame, output_path: str) -> None:
    """
    :param workbook: The workbook to be written.
    :param output_path: The path to write the workbook to.
    :returns: None
    """
    workbook.to_csv(output_path, sep="\t", index=False, encoding="utf-8")


def write_eml(eml: etree._ElementTree, output_path: str) -> None:
    """
    :param eml: The EML file to be written.
    :param output_path: The path to write the EML file to.
    :returns: None
    """
    eml.write(output_path, pretty_print=True, encoding="utf-8", xml_declaration=True)


def expand_curie(curie: str) -> str:
    """
    :param curie: The CURIE to be expanded.
    :returns: The expanded CURIE. Returns the original CURIE if the prefix
        does not have a mapping.
    """
    mapping = {
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "linkml": "https://w3id.org/linkml/",
        "ECSO": "http://purl.dataone.org/odo/ECSO_",
        "ENVO": "http://purl.obolibrary.org/obo/ENVO_",
        "BFO": "http://purl.obolibrary.org/obo/BFO_",
        "ENVTHES": "http://vocabs.lter-europe.net/EnvThes/",
        "AUTO": "AUTO:",  # return ungrounded CURIEs as is
    }
    prefix, suffix = curie.split(":")
    return f"{mapping[prefix]}{suffix}"


def compress_uri(uri: str) -> str:
    """
    Compress a URI into a CURIE based on the prefix mappings in the OBO and
    BioPortal converters.

    :param uri: The URI to be compressed into a CURIE.
    :returns: The compressed CURIE. Returns the original URI if the prefix
        does not have a mapping.
    :notes: This is a wrapper function around the `prefixmaps` and `curies`
        libraries.
    """
    converter: Converter = load_converter(["obo", "bioportal"])
    res = converter.compress(uri, passthrough=True)
    return res
