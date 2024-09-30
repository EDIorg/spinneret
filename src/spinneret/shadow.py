"""A module for creating shadow metadata"""

from urllib.parse import urljoin
from lxml import etree
from spinneret.utilities import is_uri


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
        if not is_uri(directory):
            continue

        # If the value is not a URL, then convert it to a URL
        if not is_uri(value):
            new_value = urljoin(directory, value)
            element.text = new_value

    return eml
