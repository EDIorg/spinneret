"""A module for creating shadow metadata"""

from urllib.parse import urljoin
from lxml import etree
from spinneret.utilities import is_url, load_eml, write_eml


def convert_userid_to_url(eml: etree.ElementTree) -> etree.ElementTree:
    """
    :param eml: An EML document
    :returns:   An EML document with userId elements converted to URLs, if
        not already, and if possible.
    """
    # Find all userId elements with a directory attribute
    userid_elements = eml.xpath("//userId[@directory]")

    for element in userid_elements:
        directory = element.attrib["directory"]
        value = element.text

        # If the directory isn't a URL, then there it is not possible to
        # convert the value to a URL so skip this element
        if not is_url(directory):
            continue

        # If the value is not a URL, then convert it to a URL
        if not is_url(value):
            new_value = urljoin(directory, value)
            element.text = new_value

    return eml


def create_shadow_eml(eml_path: str, output_path: str) -> None:
    """
    :param eml_path: The path to the EML file to be annotated.
    :param output_path: The path to write the annotated EML file.
    :returns: None
    :notes: This function wraps a set of enrichment functions to create a
        shadow EML file.
    """
    # Load the EML for processing
    eml = load_eml(eml_path)

    # Call each enrichment functions, passing the result of each to the next
    eml = convert_userid_to_url(eml)

    # Write eml to file
    write_eml(eml, output_path)
