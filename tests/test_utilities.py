"""Test utilities module"""

from os.path import exists
from lxml import etree
import pandas as pd
from spinneret import datasets
from spinneret.utilities import (
    delete_empty_tags,
    is_url,
    load_workbook,
    load_eml,
    write_workbook,
    write_eml,
    expand_curie,
    compress_uri,
    load_prefixmaps,
)
from spinneret.datasets import get_example_eml_dir


def test_delete_empty_tags():
    """Test that empty tags are removed from an XML file"""

    # Read test file
    eml_file = datasets.get_example_eml_dir() + "/" + "edi.3.9.xml"
    eml = load_eml(eml_file)

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


def test_load_workbook():
    """Test that a workbook is loaded as a DataFrame"""

    # Input can be a file path
    wb = load_workbook("tests/edi.3.9_annotation_workbook.tsv")
    assert isinstance(wb, pd.core.frame.DataFrame)

    # Input can be a DataFrame
    wb = pd.read_csv("tests/edi.3.9_annotation_workbook.tsv", sep="\t")
    wb = load_workbook(wb)
    assert isinstance(wb, pd.core.frame.DataFrame)


# pylint: disable=protected-access
def test_load_eml():
    """Test that an EML file is loaded as an ElementTree"""

    # Input can be a file path
    eml = load_eml(get_example_eml_dir() + "/" + "edi.3.9.xml")
    assert isinstance(eml, etree._ElementTree)

    # Input can be an ElementTree
    eml = load_eml(get_example_eml_dir() + "/" + "edi.3.9.xml")
    eml = load_eml(eml)
    assert isinstance(eml, etree._ElementTree)


def test_write_workbook(tmp_path):
    """Test that a workbook DataFrame is written to a file"""
    wb = load_workbook("tests/edi.3.9_annotation_workbook.tsv")
    output_path = str(tmp_path) + "/output.tsv"
    write_workbook(wb, output_path)
    assert exists(output_path)  # Check that the file exists
    wb2 = load_workbook(output_path)  # file contents are the same
    assert wb.equals(wb2)


def test_write_eml(tmp_path):
    """Test that an EML ElementTree is written to a file"""
    eml = load_eml(get_example_eml_dir() + "/" + "edi.3.9.xml")
    output_path = str(tmp_path) + "/edi.3.9.xml"
    write_eml(eml, output_path)
    assert exists(output_path)  # Check that the file exists
    eml2 = load_eml(output_path)  # file contents are the same
    assert etree.tostring(eml) == etree.tostring(eml2)


def test_expand_curie():
    """Test that a CURIE is expanded to a URL"""

    # Recognized CURIES should return the corresponding URI
    assert expand_curie("ECSO:00001203") == "http://purl.dataone.org/odo/ECSO_00001203"
    assert (
        expand_curie("ENVO:00001203") == "http://purl.obolibrary.org/obo/ENVO_00001203"
    )
    assert (
        expand_curie("ENVTHES:00001203")
        == "http://vocabs.lter-europe.net/EnvThes/00001203"
    )
    assert (
        expand_curie("OBOE:00001203")
        == "http://ecoinformatics.org/oboe/oboe.1.2/00001203"
    )

    # Ungrounded CURIES should return the original CURIE
    assert expand_curie("AUTO:00001203") == "AUTO:00001203"


def test_expand_curie_handles_multiple_semicolon():
    """Test that a CURIE with multiple semicolons does not raise an error

    This is an unusual case that has occurred in past integration tests. Not sure
    what the source of this issue is but are testing for it here.
    """
    curie = "ENVO:PATO:00001203"
    assert expand_curie(curie) == curie


def test_compress_uri():
    """Test that a URI is compressed to a CURIE"""

    # Return a CURIE if the URI is in the mapping
    r = compress_uri("http://purl.obolibrary.org/obo/ENVO_00001203")
    assert r == "ENVO:00001203"

    # Return the original URI if the URI is not in the mapping
    r = compress_uri("http://example.com/00001203")
    assert r == "http://example.com/00001203"


def test_load_prefixmaps():
    """Test that the prefixmaps are loaded"""
    prefixmaps = load_prefixmaps()
    assert isinstance(prefixmaps, pd.DataFrame)
