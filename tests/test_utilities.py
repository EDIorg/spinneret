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
