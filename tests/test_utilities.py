"""Test utilities module"""

from lxml import etree
from spinneret import datasets
from spinneret.utilities import delete_empty_tags, is_url


def test_delete_empty_tags():
    """Test that empty tags are removed from an XML file"""

    # Read test file
    eml_file = datasets.get_example_eml_dir() + "/" + "edi.3.9.xml"
    eml = etree.parse(eml_file)

    # Add an empty tag to the XML and check that it is added
    # to the XML
    empty_tag = etree.Element("empty_tag")
    eml.getroot().append(empty_tag)
    assert len(eml.xpath(".//empty_tag")) == 1

    # Remove empty tags
    eml = delete_empty_tags(eml)

    # Check that the empty tag has been removed
    assert len(eml.xpath(".//empty_tag")) == 0


def test_is_uri():
    """Test that a string is a URL or not"""
    assert is_url("http://purl.dataone.org/odo/ECSO_00001203") is True
    assert is_url("A free text description.") is False
