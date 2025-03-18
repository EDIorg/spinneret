"""The utilities module"""

from os import environ
from typing import Union
import importlib
from urllib.parse import urlparse
from json import load
import daiquiri

import pandas as pd
from lxml import etree

logger = daiquiri.getLogger(__name__)


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
    Expand a CURIE into a URI based on the prefix mappings in the OBO and
    BioPortal converters.

    :param curie: The CURIE to be expanded.
    :returns: The expanded CURIE. Returns the original CURIE if the prefix
        does not have a mapping.
    :notes: This is a wrapper function around the `prefixmaps` and `curies`
        libraries.
    """
    prefixmaps = load_prefixmaps()

    # On rare occasion we encounter a CURIE with multiple colons, so we need
    # to use exception handling and issue a warning.
    try:
        prefix, suffix = curie.split(":")
    except ValueError:
        logger.warning(
            f"Warning: {curie} is not recognized. Returning the original string."
        )
        return curie

    namespace = prefixmaps[prefixmaps["prefix"] == prefix]["namespace"]
    if len(namespace) > 0:
        return f"{namespace.to_string(index=False).strip()}{suffix}"
    return curie


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
    prefixmaps = load_prefixmaps()
    match = prefixmaps[prefixmaps["namespace"].apply(lambda x: x in uri)]
    if not match.empty:
        prefix = match["prefix"].values[0]
        suffix = uri.replace(match["namespace"].values[0], "")
        return f"{prefix}:{suffix}"
    return uri


def load_prefixmaps() -> dict:
    """
    Load ontology prefix maps. To be used with `expand_curie` and
    `compress_uri`.

    :returns: The ontology prefix maps
    """
    file = str(importlib.resources.files("spinneret.data")) + "/prefixmaps.csv"
    prefixmaps = pd.read_csv(file)
    return prefixmaps


def get_elements_for_predicate(eml: etree._ElementTree, predicate: str) -> list:
    """
    Get the EML elements that corresponds to a predicate. Elements contain
    the information from which annotations are derived.

    :param eml: An EML document.
    :param predicate: The predicate to be used to find the element(s).
    :returns: The element(s) that corresponds to the predicate, each as an
        etree._Element. If the predicate is not found, returns empty list.
    """
    predicate_and_xpath = {
        "contains measurements of type": "//attribute",
        "contains process": "//dataset",
        "env_broad_scale": "//dataset",
        "env_local_scale": "//dataset",
        "environmental material": "//attribute",
        "research topic": "//dataset",
        "usesMethod": "//dataset/methods",
    }
    xpath = predicate_and_xpath.get(predicate)
    if xpath:
        return eml.xpath(xpath)
    logger.warning(f"Predicate {predicate} not found in the list of predicates.")
    return []


def get_template_for_predicate(predicate: str) -> Union[str, None]:
    """
    :param predicate: The predicate to be used to find the template.
    :returns: The OntoGPT template for the predicate. Returns None if the
        predicate is not found.
    """
    predicate_and_template = {
        "contains measurements of type": "contains_measurement_of_type",
        "contains process": "contains_process",
        "env_broad_scale": "env_broad_scale",
        "env_local_scale": "env_local_scale",
        "environmental material": "env_medium",
        "research topic": "research_topic",
        "usesMethod": "uses_method",
    }
    template = predicate_and_template.get(predicate)
    if not template:
        logger.warning(f"Predicate {predicate} not found in the list of predicates.")
    return template


def get_predicate_id_for_predicate(predicate: str) -> Union[str, None]:
    """
    :param predicate: The predicate to be used to find the predicate ID.
    :returns: The predicate ID for the predicate. Returns None if the
        predicate is not found.
    """
    predicate_and_id = {
        "contains measurements of type": "http://ecoinformatics.org/oboe/"
        "oboe.1.2/oboe-core.owl#"
        "containsMeasurementsOfType",
        "contains process": "http://purl.obolibrary.org/obo/BFO_0000067",
        "env_broad_scale": "https://genomicsstandardsconsortium.github.io/mixs"
        "/0000012/",
        "env_local_scale": "https://genomicsstandardsconsortium.github.io/mixs"
        "/0000013/",
        "environmental material": "http://purl.obolibrary.org/obo/" "ENVO_00010483",
        "research topic": "http://vocabs.lter-europe.net/EnvThes/21604",
        "usesMethod": "http://ecoinformatics.org/oboe/oboe.1.2/oboe-core.owl#"
        "usesMethod",
    }
    predicate_id = predicate_and_id.get(predicate)
    if not predicate_id:
        logger.warning(f"Predicate {predicate} not found in the list of predicates.")
    return predicate_id
