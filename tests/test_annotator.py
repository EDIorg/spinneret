"""Test annotator code"""

import os
from shutil import copyfile
import pytest
import pandas as pd
from lxml import etree
from spinneret import annotator
from spinneret.annotator import (
    annotate_workbook,
    annotate_eml,
    create_annotation_element,
    add_qudt_annotations_to_workbook,
)
from spinneret.utilities import load_configuration
from spinneret.datasets import get_example_eml_dir


@pytest.mark.parametrize("use_mock", [True])  # False tests with real HTTP requests
def test_get_bioportal_annotation(mocker, use_mock, get_bioportal_annotation_fixture):
    """Test get_bioportal_annotation"""
    text = """
    This dataset contains cover of kelp forest sessile
    invertebrates, understory macroalgae, and substrate types by
    integrating data from four contributing projects working in the kelp
    forests of the Santa Barbara Channel, USA. Divers collect data on
    using either uniform point contact (UPC) or random point contact (RPC)
    methods.
    """
    if use_mock:
        # Test with mock data
        mocker.patch(
            "spinneret.annotator.get_bioportal_annotation",
            return_value=get_bioportal_annotation_fixture,
        )
        os.environ["BIOPORTAL_API_KEY"] = "mock api key"
    else:
        # Load the API key in the configuration file to enable API requests
        if not os.path.exists("config.json"):
            pytest.skip(
                "Skipping test due to missing config.json file in package root."
            )
        load_configuration("config.json")

    res = annotator.get_bioportal_annotation(
        text,
        api_key=os.environ["BIOPORTAL_API_KEY"],
        ontologies="ENVO",
        exclude_synonyms=True,
    )
    assert res is not None
    assert len(res) > 0
    assert isinstance(res, list)
    for item in res:
        assert isinstance(item, dict)
        assert "label" in item
        assert "uri" in item
        assert isinstance(item["label"], str)
        assert isinstance(item["uri"], str)
        assert item["label"] != ""
        assert item["uri"] != ""


# pylint: disable=duplicate-code
@pytest.mark.parametrize("use_mock", [True])  # False tests with real HTTP requests
def test_annotate_workbook(
    tmp_path, mocker, use_mock, get_bioportal_annotation_fixture
):
    """Test annotate_workbook"""
    if use_mock:
        # Test with mock data
        mocker.patch(
            "spinneret.annotator.get_bioportal_annotation",
            return_value=get_bioportal_annotation_fixture,
        )
        os.environ["BIOPORTAL_API_KEY"] = "mock api key"
    else:
        # Load the API key in the configuration file
        if not os.path.exists("config.json"):
            pytest.skip(
                "Skipping test due to missing config.json file in package root."
            )
        load_configuration("config.json")

    # Copy the workbook to tmp_path for editing
    wb_path = "tests/edi.3.9_annotation_workbook.tsv"
    wb_path_copy = str(tmp_path) + "/edi.3.9_annotation_workbook.tsv"
    copyfile(wb_path, wb_path_copy)
    wb_path_annotated = str(tmp_path) + "/edi.3.9_annotation_workbook_annotated.tsv"

    # Check features of the unannotated workbook
    assert os.path.exists(wb_path_copy)
    wb = pd.read_csv(wb_path_copy, sep="\t", encoding="utf-8")
    # The columns to be annotated should be empty
    cols_to_annotate = [
        "predicate",
        "predicate_id",
        "object",
        "object_id",
        "author",
        "date",
    ]
    for col in cols_to_annotate:
        assert wb[col].isnull().all()

    # Annotate the workbook copy
    annotate_workbook(
        workbook_path=wb_path_copy,
        output_path=wb_path_annotated,
    )

    # Check the workbook was annotated
    assert os.path.exists(wb_path_annotated)
    wb = pd.read_csv(wb_path_annotated, sep="\t", encoding="utf-8")
    # The columns to be annotated should be full
    for col in cols_to_annotate:
        assert not wb[col].isnull().all()


def test_annotate_eml(tmp_path):
    """Test annotate_eml"""
    eml_file = get_example_eml_dir() + "/" + "edi.3.9.xml"
    wb_file = "tests/edi.3.9_annotation_workbook_annotated.tsv"
    output_file = str(tmp_path) + "/edi.3.9_annotated.xml"

    # Check that there are no annotations in the EML file
    eml = etree.parse(eml_file)
    assert eml.xpath(".//annotation") == []

    # Annotate the EML file
    annotate_eml(eml_path=eml_file, workbook_path=wb_file, output_path=output_file)

    # Check that the EML file was annotated
    assert os.path.exists(output_file)
    eml_annotated = etree.parse(output_file)
    annotations = eml_annotated.xpath(".//annotation")
    assert annotations != []
    # The number of annotation elements should be equal to the number of rows
    # in the workbook where predicates and objects are both present.
    wb = pd.read_csv(wb_file, sep="\t", encoding="utf-8")
    num_rows = len(
        wb.dropna(subset=["predicate", "predicate_id", "object", "object_id"])
    )
    assert len(annotations) == num_rows


# pylint: disable=line-too-long
def test_create_annotation_element():
    """Test create_annotation_element"""
    fixture = """<annotation><propertyURI label="predicate_label">predicate_id</propertyURI><valueURI label="object_label">object_id</valueURI></annotation>"""
    annotation_element = create_annotation_element(
        predicate_label="predicate_label",
        predicate_id="predicate_id",
        object_label="object_label",
        object_id="object_id",
    )
    assert bytes.decode(etree.tostring(annotation_element)) == fixture


@pytest.mark.parametrize("use_mock", [True])  # False makes real HTTP requests
def test_get_qudt_annotation(use_mock, mocker):
    """Test get_qudt_annotation"""

    # A mappable unit returns the QUDT equivalent
    if use_mock:
        mocker.patch(
            "spinneret.annotator.get_qudt_annotation",
            return_value=[{"label": "Meter", "uri": "http://qudt.org/vocab/unit/M"}],
        )
    r = annotator.get_qudt_annotation("meter")
    assert r[0]["label"] == "Meter"
    assert r[0]["uri"] == "http://qudt.org/vocab/unit/M"

    # An unmappable unit returns None
    if use_mock:
        mocker.patch(
            "spinneret.annotator.get_qudt_annotation",
            return_value=None,
        )
    r = annotator.get_qudt_annotation("Martha Stewart")
    assert r is None


@pytest.mark.parametrize("use_mock", [True])  # False makes real HTTP requests
def test_add_qudt_annotations_to_workbook(tmp_path, use_mock, mocker):
    """Test add_qudt_annotations_to_workbook"""

    # Parameterize the test
    workbook_path = "tests/edi.3.9_annotation_workbook.tsv"
    output_path = str(tmp_path) + "edi.3.9_annotation_workbook_qudt.tsv"

    # The workbook shouldn't have any annotations yet
    wb = pd.read_csv(workbook_path, sep="\t", encoding="utf-8")
    assert wb["object_id"].isnull().all()

    # The workbook has annotations after calling the function
    if use_mock:
        mocker.patch(  # a response returned in real requests
            "spinneret.annotator.get_qudt_annotation",
            return_value=[
                {"label": "latitude", "uri": "http://qudt.org/vocab/unit/DEG"}
            ],
        )
    add_qudt_annotations_to_workbook(
        workbook_path=workbook_path,
        eml_path=get_example_eml_dir() + "/" + "edi.3.9.xml",
        output_path=output_path,
    )
    wb = pd.read_csv(output_path, sep="\t", encoding="utf-8")
    assert not wb["object_id"].isnull().all()
    assert not wb["object"].isnull().all()
    assert not wb["predicate_id"].isnull().all()
    assert not wb["predicate"].isnull().all()

    # Overwriting changes the annotations. Note, we can't test this with real
    # requests because we'll expect the same results as the first call.
    if use_mock:
        mocker.patch(  # an arbitrary response to check for
            "spinneret.annotator.get_qudt_annotation",
            return_value=[
                {
                    "label": "Martha_Stewart",
                    "uri": "http://qudt.org/vocab/unit/Martha_Stewart",
                }
            ],
        )
        add_qudt_annotations_to_workbook(
            workbook_path=output_path,  # the output from the first call
            eml_path=get_example_eml_dir() + "/" + "edi.3.9.xml",
            output_path=output_path,
            overwrite=True,
        )
        wb = pd.read_csv(output_path, sep="\t", encoding="utf-8")
        assert "Martha_Stewart" in wb["object"].values
        assert "http://qudt.org/vocab/unit/Martha_Stewart" in wb["object_id"].values
        # Original annotations are gone
        assert "latitude" not in wb["object"].values
        assert "http://qudt.org/vocab/unit/DEG" not in wb["object_id"].values
