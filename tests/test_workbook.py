"""Test workbook code"""

import os
import tempfile
from time import sleep
import pandas as pd
from spinneret import workbook
from spinneret import datasets
from spinneret.workbook import (
    get_description,
    initialize_workbook_row,
    list_workbook_columns,
    get_package_id,
    get_package_url,
    create,
    delete_duplicate_annotations,
    delete_annotations,
    delete_unannotated_rows,
    is_unannotated_row,
)
from spinneret.utilities import load_eml, load_workbook


def test_create():
    """Test workbook creation and attributes"""

    # A workbook is created for each EML file
    eml_file = datasets.get_example_eml_dir() + "/" + "edi.3.9.xml"
    with tempfile.TemporaryDirectory() as tmpdir:
        wb = workbook.create(
            eml_file=eml_file,
            elements=["dataset", "dataTable", "otherEntity", "attribute"],
            path_out=tmpdir,
        )
        eml_file_name = os.path.basename(eml_file)
        package_id = os.path.splitext(eml_file_name)[0]
        wb_path = tmpdir + "/" + package_id + "_annotation_workbook.tsv"
        assert os.path.isfile(wb_path)
        assert isinstance(wb, pd.core.frame.DataFrame)
        assert len(wb.package_id.unique()) == 1

        # Test workbook attributes against fixture
        wbf = load_workbook("tests/edi.3.9_annotation_workbook.tsv")
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
    eml = load_eml(eml_file)

    # Elements to test (note dataTable is a general test for data entities)
    elements = ["dataset", "dataTable", "attribute", "methods"]

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
    eml = load_eml(eml_file)

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
    assert res.to_list() == [pd.NA] * len(res)


def test_get_package_id():
    """Test the get_package_id function"""
    eml_file = datasets.get_example_eml_dir() + "/" + "edi.3.9.xml"
    eml = load_eml(eml_file)
    assert get_package_id(eml) == "edi.3.9"


def test_get_package_url():
    """Test the get_package_url function"""

    # Default environment is production
    eml_file = datasets.get_example_eml_dir() + "/" + "edi.3.9.xml"
    eml = load_eml(eml_file)
    expected_url = (
        "https://portal.edirepository.org/nis/metadataviewer?packageid=edi.3.9"
    )
    assert get_package_url(eml) == expected_url

    # Specify a different environment to get its URL
    expected_url = (
        "https://portal-s.edirepository.org/nis/metadataviewer?packageid=edi.3.9"
    )
    assert get_package_url(eml, env="staging") == expected_url


def test_delete_duplicate_annotations():
    """Test the delete_duplicate_annotations function"""

    # Create a workbook with duplicate annotations
    eml_file = datasets.get_example_eml_dir() + "/" + "edi.3.9.xml"
    wb = create(
        eml_file=eml_file,
        elements=["dataset"],
    )
    # Row 1
    wb.loc[0, "predicate"] = "predicate"
    wb.loc[0, "predicate_id"] = "predicate_id"
    wb.loc[0, "object"] = "object"
    wb.loc[0, "object_id"] = "object_id"
    wb.loc[0, "date"] = pd.Timestamp.now()
    # Row 2 is a duplicate annotation of row 1
    row = wb.iloc[0].copy()
    wb.loc[len(wb)] = row
    sleep(1)  # pause for 1 second to ensure the datetime is different
    wb.loc[1, "date"] = pd.Timestamp.now()

    # Test that the duplicate annotation is removed and the newest annotation
    # is kept
    newest_date = wb.loc[1, "date"]
    wb = delete_duplicate_annotations(wb)
    assert len(wb) == 1
    assert wb.loc[1, "date"] == newest_date


def test_delete_annotations():
    """Test delete_annotations based on filter parameters"""

    # A simple workbook for testing
    row1 = initialize_workbook_row()
    row1["element"] = "dataset"
    row1["object_id"] = "http://purl.obolibrary.org/obo/ENVO_00000015"
    row1["author"] = "BioPortal Annotator"
    row2 = initialize_workbook_row()
    row2["element"] = "dataset"
    row2["object_id"] = "http://purl.obolibrary.org/obo/ENVO_00001253"
    row2["author"] = "http://orcid.org/xxxx-xxxx-xxxx-xxxx"
    wb = pd.DataFrame([row1, row2])

    # Remove annotations based on one filter parameter
    # Check that the criteria exist before deletion
    assert any("ENVO" in str(x) for x in wb["object_id"])
    new_wb = delete_annotations(wb, {"object_id": "ENVO"})
    # Check that the matching criteria are removed
    assert not any("ENVO" in str(x) for x in new_wb["object_id"])
    assert len(new_wb) == 0  # all rows contained the criteria

    # Remove annotations based on multiple filter parameters
    # Check that the criteria exist before deletion
    assert any("ENVO" in str(x) for x in wb["object_id"])
    assert any("BioPortal Annotator" in str(x) for x in wb["author"])
    criteria = {"object_id": "ENVO", "author": "BioPortal Annotator"}
    new_wb = delete_annotations(wb, criteria)
    # Check that the matching criteria are removed
    assert any("ENVO" in str(x) for x in wb["object_id"])
    assert not any("BioPortal Annotator" in str(x) for x in new_wb["object_id"])
    assert len(new_wb) == 1  # not all rows met these criteria


def test_delete_unannotated_rows(annotated_workbook):
    """Test delete_unannotated_rows function"""

    # Workbook fixture has unannotated rows
    wb = annotated_workbook
    # Use list comprehension to check for unannotated rows
    unannotated_rows = [is_unannotated_row(row) for index, row in wb.iterrows()]
    assert any(unannotated_rows)

    # Unannotated rows are removed by calling delete_unannotated_rows
    wb = delete_unannotated_rows(wb)
    unannotated_rows = [is_unannotated_row(row) for index, row in wb.iterrows()]
    assert not any(unannotated_rows)

    # Workbooks with no unannotated rows are unchanged
    wb2 = delete_unannotated_rows(wb)
    assert wb.equals(wb2)

    # Completely unannotated workbooks will have all rows removed
    wb = pd.DataFrame([initialize_workbook_row()])
    assert len(wb) == 1


def test_is_unannotated():
    """Test is_unannotated_row function"""

    # A row with no annotation components is unannotated
    wb = pd.DataFrame([initialize_workbook_row()])
    row = wb.iloc[0]
    assert is_unannotated_row(row)

    # A row with incomplete annotation components is unannotated
    wb = pd.DataFrame([initialize_workbook_row()])
    row = wb.iloc[0]
    wb.loc[0, "predicate"] = "predicate"
    wb.loc[0, "predicate_id"] = "predicate_id"
    assert is_unannotated_row(row)

    # A row with all annotation components is not unannotated
    wb = pd.DataFrame([initialize_workbook_row()])
    wb.loc[0, "predicate"] = "predicate"
    wb.loc[0, "predicate_id"] = "predicate_id"
    wb.loc[0, "object"] = "object"
    wb.loc[0, "object_id"] = "object_id"
    row = wb.iloc[0]
    assert not is_unannotated_row(row)
