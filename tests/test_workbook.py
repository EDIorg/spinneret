"""Test workbook code"""

import os
import tempfile
import pandas as pd
from lxml import etree
from spinneret import workbook
from spinneret import datasets
from spinneret.workbook import (
    get_description,
    initialize_workbook_row,
    list_workbook_columns,
    get_package_id,
    get_package_url,
)


def test_create():
    """Test workbook creation and attributes"""

    # A workbook is created for each EML file
    eml_dir = datasets.get_example_eml_dir()
    eml_file = eml_dir + "/" + "edi.3.9.xml"
    with tempfile.TemporaryDirectory() as tmpdir:
        wb = workbook.create(
            eml_file=eml_file,
            elements=["dataset", "dataTable", "otherEntity", "attribute"],
            base_url="https://portal.edirepository.org/nis/metadataviewer?packageid=",
            path_out=tmpdir,
        )
        eml_file_name = os.path.basename(eml_file)
        package_id = os.path.splitext(eml_file_name)[0]
        wb_path = tmpdir + "/" + package_id + "_annotation_workbook.tsv"
        assert os.path.isfile(wb_path)
        assert isinstance(wb, pd.core.frame.DataFrame)
        assert len(wb.package_id.unique()) == 1

        # Test workbook attributes against fixture
        wbf = pd.read_csv("tests/edi.3.9_annotation_workbook.tsv", sep="\t").fillna("")
        cols = wb.columns.to_list()
        for c in cols:
            if c != "element_id":  # new UUIDs won't match the fixture
                assert sorted(wb[c].unique()) == sorted(wbf[c].unique())


def test_get_description():
    """Test that the get_description function returns a description for each
    element"""
    # Read test file
    eml_dir = datasets.get_example_eml_dir()
    eml_file = eml_dir + "/" + "edi.3.9.xml"
    eml = etree.parse(eml_file)

    # Elements to test (note dataTable is a general test for data entities)
    elements = ["dataset", "dataTable", "attribute"]

    # Test each element
    for element in elements:
        element = eml.xpath(".//" + element)[0]
        description = get_description(element)
        assert isinstance(description, str)
        assert len(description) > 0


def test_get_description_handles_missing_element():
    """Test that the get_description function returns an empty string when the
    optional elements are missing"""

    # Read test file
    eml_file = datasets.get_example_eml_dir() + "/" + "edi.3.9.xml"
    eml = etree.parse(eml_file)

    # Remove abstract and keywordSet elements from dataset
    element = eml.xpath(".//dataset")[0]
    element.remove(element.find("abstract"))
    for kw in element.findall(".//keywordSet"):
        element.remove(kw)

    # Test element with missing abstract
    description = get_description(element)
    assert description == ""


def test_list_workbook_columns():
    """Test the list_workbook_columns function"""
    res = list_workbook_columns()
    assert isinstance(res, list)
    assert len(res) > 0


def test_initialize_workbook_row():
    """Test the initialize_workbook_row function"""
    res = initialize_workbook_row()
    assert isinstance(res, pd.core.series.Series)
    assert res.index.to_list() == list_workbook_columns()
    assert res.to_list() == [""] * len(res)


def test_get_package_id():
    """Test the get_package_id function"""
    eml_file = datasets.get_example_eml_dir() + "/" + "edi.3.9.xml"
    eml = etree.parse(eml_file)
    assert get_package_id(eml) == "edi.3.9"


def test_get_package_url():
    """Test the get_package_url function"""

    # Default environment is production
    eml_file = datasets.get_example_eml_dir() + "/" + "edi.3.9.xml"
    eml = etree.parse(eml_file)
    expected_url = (
        "https://portal.edirepository.org/nis/metadataviewer?packageid=edi.3.9"
    )
    assert get_package_url(eml) == expected_url

    # Specify a different environment to get its URL
    expected_url = (
        "https://portal-s.edirepository.org/nis/metadataviewer?packageid=edi.3.9"
    )
    assert get_package_url(eml, env="staging") == expected_url
