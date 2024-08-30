"""Test annotator code"""

import os
from shutil import copyfile
import pytest
import pandas as pd
from lxml import etree
from spinneret.annotator import (
    get_bioportal_annotation,
    annotate_workbook,
    annotate_eml,
    create_annotation_element,
)
from spinneret.utilities import load_configuration
from spinneret.datasets import get_example_eml_dir


def test_get_bioportal_annotation():
    """Test get_bioportal_annotation"""
    text = """
    This dataset contains cover of kelp forest sessile
    invertebrates, understory macroalgae, and substrate types by
    integrating data from four contributing projects working in the kelp
    forests of the Santa Barbara Channel, USA. Divers collect data on
    using either uniform point contact (UPC) or random point contact (RPC)
    methods.
    """
    if not os.path.exists("config.json"):
        pytest.skip("Skipping test due to missing config.json file in package root.")
    load_configuration("config.json")
    res = get_bioportal_annotation(
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
def test_annotate_workbook(tmp_path):
    """Test annotate_workbook"""
    # Load the API key in the configuration file
    if not os.path.exists("config.json"):
        pytest.skip("Skipping test due to missing config.json file in package root.")
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
