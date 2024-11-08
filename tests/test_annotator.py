"""Test annotator code"""

import os
from shutil import copyfile

import pandas as pd
import pytest
from lxml import etree
from spinneret import annotator
from spinneret.annotator import (
    annotate_workbook,
    annotate_eml,
    create_annotation_element,
    add_qudt_annotations_to_workbook,
    add_dataset_annotations_to_workbook,
    add_measurement_type_annotations_to_workbook,
    add_process_annotations_to_workbook,
    add_env_broad_scale_annotations_to_workbook,
    add_env_local_scale_annotations_to_workbook,
    add_env_medium_annotations_to_workbook,
    add_research_topic_annotations_to_workbook,
    add_methods_annotations_to_workbook,
)
from spinneret.utilities import load_configuration, load_eml, load_workbook
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
    wb = load_workbook(wb_path_copy)
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
        eml_path=get_example_eml_dir() + "/" + "edi.3.9.xml",
        output_path=wb_path_annotated,
    )

    # Check the workbook was annotated
    assert os.path.exists(wb_path_annotated)
    wb = load_workbook(wb_path_annotated)
    # The columns to be annotated should be full
    for col in cols_to_annotate:
        assert not wb[col].isnull().all()


def test_annotate_eml(tmp_path):
    """Test annotate_eml"""
    eml_file = get_example_eml_dir() + "/" + "edi.3.9.xml"
    wb_file = "tests/edi.3.9_annotation_workbook_annotated.tsv"
    output_file = str(tmp_path) + "/edi.3.9_annotated.xml"

    # Check that there are no annotations in the EML file
    eml = load_eml(eml_file)
    assert eml.xpath(".//annotation") == []

    # Annotate the EML file
    annotate_eml(eml_path=eml_file, workbook_path=wb_file, output_path=output_file)

    # Check that the EML file was annotated
    assert os.path.exists(output_file)
    eml_annotated = load_eml(output_file)
    annotations = eml_annotated.xpath(".//annotation")
    assert annotations != []
    # The number of annotation elements should be equal to the number of rows
    # in the workbook where predicates and objects are both present.
    wb = load_workbook(wb_file)
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
    wb = load_workbook(workbook_path)
    assert not has_annotations(wb)

    # The workbook has annotations after calling the function
    if use_mock:
        mocker.patch(
            "spinneret.annotator.get_qudt_annotation",
            return_value=[
                {"label": "latitude", "uri": "http://qudt.org/vocab/unit/DEG"}
            ],
        )
    wb = add_qudt_annotations_to_workbook(
        workbook=workbook_path,
        eml=get_example_eml_dir() + "/" + "edi.3.9.xml",
        output_path=output_path,
    )
    assert has_annotations(wb)

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
        wb = add_qudt_annotations_to_workbook(
            workbook=output_path,  # the output from the first call
            eml=get_example_eml_dir() + "/" + "edi.3.9.xml",
            output_path=output_path,
            overwrite=True,
        )
        assert wb["object"].str.contains("Martha_Stewart").any()
        assert (
            wb["object_id"]
            .str.contains("http://qudt.org/vocab/unit/Martha_Stewart")
            .any()
        )

        # Original annotations are gone
        assert not wb["object"].str.contains("latitude").any()
        assert not wb["object_id"].str.contains("http://qudt.org/vocab/unit/DEG").any()


def test_add_qudt_annotations_to_workbook_io_options(tmp_path, mocker):
    """Test add_qudt_annotations_to_workbook with different input and output
    options"""

    mocker.patch(
        "spinneret.annotator.get_qudt_annotation",
        return_value=[{"label": "latitude", "uri": "http://qudt.org/vocab/unit/DEG"}],
    )

    # Accepts file path as input
    output_path = str(tmp_path) + "edi.3.9_annotation_workbook_qudt.tsv"
    wb = add_qudt_annotations_to_workbook(
        workbook="tests/edi.3.9_annotation_workbook.tsv",
        eml=get_example_eml_dir() + "/" + "edi.3.9.xml",
        output_path=output_path,
    )
    wb = load_workbook(output_path)
    assert has_annotations(wb)

    # Accepts dataframes and etree objects as input
    wb = load_workbook("tests/edi.3.9_annotation_workbook.tsv")
    eml = load_eml(get_example_eml_dir() + "/" + "edi.3.9.xml")
    wb = add_qudt_annotations_to_workbook(workbook=wb, eml=eml)
    assert has_annotations(wb)


def has_annotations(workbook):
    """
    :param workbook: pd.DataFrame
    :return: True if the workbook has annotations, False otherwise.
    :notes: The workbook has annotations if the columns `predicate`,
    `predicate_id`, `object` and `object_id` are not all null.
    """
    annotation_cols = workbook[["predicate", "predicate_id", "object", "object_id"]]
    return not annotation_cols.isnull().all().all()


def test_has_annotations():
    """Test the has_annotations helper function"""

    # The empty workbook has no annotations
    wb = load_workbook("tests/edi.3.9_annotation_workbook.tsv")
    assert has_annotations(wb) is False

    # The workbook with annotations has annotations
    wb = load_workbook("tests/edi.3.9_annotation_workbook_annotated.tsv")
    assert has_annotations(wb) is True


@pytest.mark.parametrize("use_mock", [True])  # False makes real HTTP requests
def test_add_dataset_annotations_to_workbook(tmp_path, use_mock, mocker):
    """Test add_dataset_annotations_to_workbook"""

    # Parameterize the test
    workbook_path = "tests/edi.3.9_annotation_workbook.tsv"
    output_path = str(tmp_path) + "edi.3.9_annotation_workbook_qudt.tsv"

    # The workbook shouldn't have any annotations yet
    wb = load_workbook(workbook_path)
    assert not has_annotations(wb)

    # The workbook has annotations after calling the function
    if use_mock:
        mocker.patch(
            "spinneret.annotator.get_bioportal_annotation",
            return_value=[
                {
                    "label": "freshwater lake biome",
                    "uri": "http://purl.obolibrary.org/obo/ENVO_01000252",
                }
            ],
        )
        os.environ["BIOPORTAL_API_KEY"] = "mock api key"
    wb = add_dataset_annotations_to_workbook(
        workbook=workbook_path,
        eml=get_example_eml_dir() + "/" + "edi.3.9.xml",
        output_path=output_path,
    )
    assert has_annotations(wb)

    # Overwriting changes the annotations. Note, we can't test this with real
    # requests because we'll expect the same results as the first call.
    if use_mock:
        mocker.patch(  # an arbitrary response to check for
            "spinneret.annotator.get_bioportal_annotation",
            return_value=[
                {
                    "label": "A different biome",
                    "uri": "http://purl.obolibrary.org/obo/ENVO_XXXXXXXX",
                }
            ],
        )
        os.environ["BIOPORTAL_API_KEY"] = "mock api key"
    wb = add_dataset_annotations_to_workbook(
        workbook=output_path,  # the output from the first call
        eml=get_example_eml_dir() + "/" + "edi.3.9.xml",
        output_path=output_path,
        overwrite=True,
    )
    assert wb["object"].str.contains("A different biome").any()
    assert (
        wb["object_id"]
        .str.contains("http://purl.obolibrary.org/obo/ENVO_XXXXXXXX")
        .any()
    )

    # Original annotations are gone
    assert not wb["object"].str.contains("freshwater lake biome").any()
    assert (
        not wb["object_id"]
        .str.contains("http://purl.obolibrary.org/obo/ENVO_01000252")
        .any()
    )


def test_add_dataset_annotations_to_workbook_io_options(tmp_path, mocker):
    """Test add_dataset_annotations_to_workbook with different input and output
    options"""

    mocker.patch(
        "spinneret.annotator.get_bioportal_annotation",
        return_value=[
            {
                "label": "freshwater lake biome",
                "uri": "http://purl.obolibrary.org/obo/ENVO_01000252",
            }
        ],
    )
    os.environ["BIOPORTAL_API_KEY"] = "mock api key"

    # Accepts file path as input
    output_path = str(tmp_path) + "edi.3.9_annotation_workbook_dataset.tsv"
    wb = add_dataset_annotations_to_workbook(
        workbook="tests/edi.3.9_annotation_workbook.tsv",
        eml=get_example_eml_dir() + "/" + "edi.3.9.xml",
        output_path=output_path,
    )
    wb = load_workbook(output_path)
    assert has_annotations(wb)

    # Accepts dataframes and etree objects as input
    wb = load_workbook("tests/edi.3.9_annotation_workbook.tsv")
    eml = load_eml(get_example_eml_dir() + "/" + "edi.3.9.xml")
    wb = add_dataset_annotations_to_workbook(workbook=wb, eml=eml)
    assert has_annotations(wb)


@pytest.mark.parametrize("use_mock", [True])  # False makes real HTTP requests
def test_add_measurement_type_annotations_to_workbook(tmp_path, use_mock, mocker):
    """Test add_measurement_type_annotations_to_workbook"""

    # Parameterize the test
    workbook_path = "tests/edi.3.9_annotation_workbook.tsv"
    output_path = str(tmp_path) + "edi.3.9_annotation_workbook_qudt.tsv"

    # The workbook shouldn't have any annotations yet
    wb = load_workbook(workbook_path)
    assert not has_annotations(wb)

    # The workbook has annotations after calling the function
    if use_mock:
        mocker.patch(
            "spinneret.annotator.get_bioportal_annotation",
            return_value=[
                {
                    "label": "depth",
                    "uri": "http://purl.dataone.org/odo/ECSO_00000515",
                }
            ],
        )
        os.environ["BIOPORTAL_API_KEY"] = "mock api key"
    wb = add_measurement_type_annotations_to_workbook(
        workbook=workbook_path,
        eml=get_example_eml_dir() + "/" + "edi.3.9.xml",
        output_path=output_path,
    )
    assert has_annotations(wb)

    # Overwriting changes the annotations. Note, we can't test this with real
    # requests because we'll expect the same results as the first call.
    if use_mock:
        mocker.patch(  # an arbitrary response to check for
            "spinneret.annotator.get_bioportal_annotation",
            return_value=[
                {
                    "label": "A different measurement type",
                    "uri": "http://purl.dataone.org/odo/ECSO_XXXXXXXX",
                }
            ],
        )
        os.environ["BIOPORTAL_API_KEY"] = "mock api key"
    wb = add_measurement_type_annotations_to_workbook(
        workbook=output_path,  # the output from the first call
        eml=get_example_eml_dir() + "/" + "edi.3.9.xml",
        output_path=output_path,
        overwrite=True,
    )
    assert wb["object"].str.contains("A different measurement type").any()
    assert (
        wb["object_id"].str.contains("http://purl.dataone.org/odo/ECSO_XXXXXXXX").any()
    )

    # Original annotations are gone
    assert not wb["object"].str.contains("depth").any()
    assert (
        not wb["object_id"]
        .str.contains("http://purl.dataone.org/odo/ECSO_00000515")
        .any()
    )


def test_add_measurement_type_annotations_to_workbook_io_options(tmp_path, mocker):
    """Test add_measurement_type_annotations_to_workbook with different input
    and output options"""

    mocker.patch(
        "spinneret.annotator.get_bioportal_annotation",
        return_value=[
            {
                "label": "depth",
                "uri": "http://purl.dataone.org/odo/ECSO_00000515",
            }
        ],
    )
    os.environ["BIOPORTAL_API_KEY"] = "mock api key"

    # Accepts file path as input
    output_path = str(tmp_path) + "edi.3.9_annotation_workbook_dataset.tsv"
    wb = add_measurement_type_annotations_to_workbook(
        workbook="tests/edi.3.9_annotation_workbook.tsv",
        eml=get_example_eml_dir() + "/" + "edi.3.9.xml",
        output_path=output_path,
    )
    wb = load_workbook(output_path)
    assert has_annotations(wb)

    # Accepts dataframes and etree objects as input
    wb = load_workbook("tests/edi.3.9_annotation_workbook.tsv")
    eml = load_eml(get_example_eml_dir() + "/" + "edi.3.9.xml")
    wb = add_measurement_type_annotations_to_workbook(workbook=wb, eml=eml)
    assert has_annotations(wb)


def test_annotators_are_listed_as_authors(tmp_path, mocker):
    """Test that the annotators are listed as authors in the workbook. Test
    this for each workbook annotator with an annotator parameter."""

    # Test for the `add_measurement_type_annotations_to_workbook` function
    # using the OntoGPT annotator
    mocker.patch(
        "spinneret.annotator.get_ontogpt_annotation",
        return_value=[{"label": "a label", "uri": "a uri"}],
    )
    wb = add_measurement_type_annotations_to_workbook(
        workbook="tests/edi.3.9_annotation_workbook.tsv",
        eml=get_example_eml_dir() + "/" + "edi.3.9.xml",
        output_path=str(tmp_path) + "edi.3.9_annotation_workbook_dataset.tsv",
        annotator="ontogpt",
        local_model="llama3.2",
    )
    authors = wb["author"].unique()
    authors = [x for x in authors if pd.notna(x)]
    assert "spinneret.annotator.get_ontogpt_annotation" == authors[0]

    # Test for the `add_measurement_type_annotations_to_workbook` function
    # using the Bioportal annotator
    mocker.patch(
        "spinneret.annotator.get_bioportal_annotation",
        return_value=[{"label": "a label", "uri": "a uri"}],
    )
    os.environ["BIOPORTAL_API_KEY"] = "mock api key"
    wb = add_measurement_type_annotations_to_workbook(
        workbook="tests/edi.3.9_annotation_workbook.tsv",
        eml=get_example_eml_dir() + "/" + "edi.3.9.xml",
        output_path=str(tmp_path) + "edi.3.9_annotation_workbook_dataset.tsv",
        annotator="bioportal",
    )
    authors = wb["author"].unique()
    authors = [x for x in authors if pd.notna(x)]
    assert "spinneret.annotator.get_bioportal_annotation" == authors[0]


@pytest.mark.parametrize("use_mock", [True])  # False tests with real local LLM queries
def test_get_ontogpt_annotation(mocker, use_mock):
    """Test get_ontogpt_annotation"""

    if use_mock:
        mocker.patch(
            "spinneret.annotator.get_ontogpt_annotation",
            return_value=[
                {
                    "label": "temperate environment",
                    "uri": "http://purl.obolibrary.org/obo/ENVO_01001705",
                },
                {
                    "label": "freshwater lake biome",
                    "uri": "http://purl.obolibrary.org/obo/ENVO_01000252",
                },
            ],
        )

    with open("tests/data/ontogpt/input/abstract.txt", "r", encoding="utf-8") as file:
        res = annotator.get_ontogpt_annotation(
            text=file.read(),
            template="env_broad_scale",
            local_model="llama3.2",
            return_ungrounded=True,
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


@pytest.mark.parametrize("use_mock", [True])  # False tests with real local LLM queries
def test_add_process_annotations_to_workbook(tmp_path, use_mock, mocker):
    """Test add_process_annotations_to_workbook"""

    # Parameterize the test
    workbook_path = "tests/edi.3.9_annotation_workbook.tsv"
    output_path = str(tmp_path) + "edi.3.9_annotation_workbook_qudt.tsv"

    # The workbook shouldn't have any annotations yet
    wb = load_workbook(workbook_path)
    assert not has_annotations(wb)

    # The workbook has annotations after calling the function
    if use_mock:
        mocker.patch(
            "spinneret.annotator.get_ontogpt_annotation",
            return_value=[{"label": "a label", "uri": "a uri"}],
        )
    wb = add_process_annotations_to_workbook(
        workbook=workbook_path,
        eml=get_example_eml_dir() + "/" + "edi.3.9.xml",
        output_path=output_path,
        local_model="llama3.2",
        return_ungrounded=True,  # ensures we get at least one annotation back
    )
    assert has_annotations(wb)

    # Overwriting changes the annotations. Note, we can't test this with real
    # requests because we'll expect the same results as the first call.
    if use_mock:
        mocker.patch(  # an arbitrary response to check for
            "spinneret.annotator.get_ontogpt_annotation",
            return_value=[{"label": "a different label", "uri": "a different uri"}],
        )
    wb = add_process_annotations_to_workbook(
        workbook=output_path,  # the output from the first call
        eml=get_example_eml_dir() + "/" + "edi.3.9.xml",
        output_path=output_path,
        local_model="llama3.2",
        return_ungrounded=True,  # ensures we get at least one annotation back
        overwrite=True,
    )
    assert wb["object"].str.contains("a different label").any()
    assert wb["object_id"].str.contains("a different uri").any()

    # Original annotations are gone
    assert not wb["object"].str.contains("a label").any()
    assert not wb["object_id"].str.contains("a uri").any()


@pytest.mark.parametrize("use_mock", [True])  # False tests with real local LLM queries
def test_add_env_broad_scale_annotations_to_workbook(tmp_path, use_mock, mocker):
    """Test add_env_broad_scale_annotations_to_workbook"""

    # Parameterize the test
    workbook_path = "tests/edi.3.9_annotation_workbook.tsv"
    output_path = str(tmp_path) + "edi.3.9_annotation_workbook.tsv"

    # The workbook shouldn't have any annotations yet
    wb = load_workbook(workbook_path)
    assert not has_annotations(wb)

    # The workbook has annotations after calling the function
    if use_mock:
        mocker.patch(
            "spinneret.annotator.get_ontogpt_annotation",
            return_value=[{"label": "a label", "uri": "a uri"}],
        )
    wb = add_env_broad_scale_annotations_to_workbook(
        workbook=workbook_path,
        eml=get_example_eml_dir() + "/" + "edi.3.9.xml",
        output_path=output_path,
        local_model="llama3.2",
        return_ungrounded=True,  # ensures we get at least one annotation back
    )
    assert has_annotations(wb)

    # Overwriting changes the annotations. Note, we can't test this with real
    # requests because we'll expect the same results as the first call.
    if use_mock:
        mocker.patch(  # an arbitrary response to check for
            "spinneret.annotator.get_ontogpt_annotation",
            return_value=[{"label": "a different label", "uri": "a different uri"}],
        )
    wb = add_env_broad_scale_annotations_to_workbook(
        workbook=output_path,  # the output from the first call
        eml=get_example_eml_dir() + "/" + "edi.3.9.xml",
        output_path=output_path,
        local_model="llama3.2",
        return_ungrounded=True,  # ensures we get at least one annotation back
        overwrite=True,
    )
    assert wb["object"].str.contains("a different label").any()
    assert wb["object_id"].str.contains("a different uri").any()

    # Original annotations are gone
    assert not wb["object"].str.contains("a label").any()
    assert not wb["object_id"].str.contains("a uri").any()


@pytest.mark.parametrize("use_mock", [True])  # False tests with real local LLM queries
def test_add_env_local_scale_annotations_to_workbook(tmp_path, use_mock, mocker):
    """Test add_env_local_scale_annotations_to_workbook"""

    # Parameterize the test
    workbook_path = "tests/edi.3.9_annotation_workbook.tsv"
    output_path = str(tmp_path) + "edi.3.9_annotation_workbook.tsv"

    # The workbook shouldn't have any annotations yet
    wb = load_workbook(workbook_path)
    assert not has_annotations(wb)

    # The workbook has annotations after calling the function
    if use_mock:
        mocker.patch(
            "spinneret.annotator.get_ontogpt_annotation",
            return_value=[{"label": "a label", "uri": "a uri"}],
        )
    wb = add_env_local_scale_annotations_to_workbook(
        workbook=workbook_path,
        eml=get_example_eml_dir() + "/" + "edi.3.9.xml",
        output_path=output_path,
        local_model="llama3.2",
        return_ungrounded=True,  # ensures we get at least one annotation back
    )
    assert has_annotations(wb)

    # Overwriting changes the annotations. Note, we can't test this with real
    # requests because we'll expect the same results as the first call.
    if use_mock:
        mocker.patch(  # an arbitrary response to check for
            "spinneret.annotator.get_ontogpt_annotation",
            return_value=[{"label": "a different label", "uri": "a different uri"}],
        )
    wb = add_env_local_scale_annotations_to_workbook(
        workbook=output_path,  # the output from the first call
        eml=get_example_eml_dir() + "/" + "edi.3.9.xml",
        output_path=output_path,
        local_model="llama3.2",
        return_ungrounded=True,  # ensures we get at least one annotation back
        overwrite=True,
    )
    assert wb["object"].str.contains("a different label").any()
    assert wb["object_id"].str.contains("a different uri").any()

    # Original annotations are gone
    assert not wb["object"].str.contains("a label").any()
    assert not wb["object_id"].str.contains("a uri").any()


@pytest.mark.parametrize("use_mock", [True])  # False tests with real local LLM queries
def test_add_env_medium_annotations_to_workbook(tmp_path, use_mock, mocker):
    """Test add_env_medium_annotations_to_workbook"""

    # Parameterize the test
    workbook_path = "tests/edi.3.9_annotation_workbook.tsv"
    output_path = str(tmp_path) + "edi.3.9_annotation_workbook.tsv"

    # The workbook shouldn't have any annotations yet
    wb = load_workbook(workbook_path)
    assert not has_annotations(wb)

    # The workbook has annotations after calling the function
    if use_mock:
        mocker.patch(
            "spinneret.annotator.get_ontogpt_annotation",
            return_value=[{"label": "a label", "uri": "a uri"}],
        )
    wb = add_env_medium_annotations_to_workbook(
        workbook=workbook_path,
        eml=get_example_eml_dir() + "/" + "edi.3.9.xml",
        output_path=output_path,
        local_model="llama3.2",
        return_ungrounded=True,  # ensures we get at least one annotation back
    )
    assert has_annotations(wb)

    # Overwriting changes the annotations. Note, we can't test this with real
    # requests because we'll expect the same results as the first call.
    if use_mock:
        mocker.patch(  # an arbitrary response to check for
            "spinneret.annotator.get_ontogpt_annotation",
            return_value=[{"label": "a different label", "uri": "a different uri"}],
        )
    wb = add_env_medium_annotations_to_workbook(
        workbook=output_path,  # the output from the first call
        eml=get_example_eml_dir() + "/" + "edi.3.9.xml",
        output_path=output_path,
        local_model="llama3.2",
        return_ungrounded=True,  # ensures we get at least one annotation back
        overwrite=True,
    )
    assert wb["object"].str.contains("a different label").any()
    assert wb["object_id"].str.contains("a different uri").any()

    # Original annotations are gone
    assert not wb["object"].str.contains("a label").any()
    assert not wb["object_id"].str.contains("a uri").any()


@pytest.mark.parametrize("use_mock", [True])  # False tests with real local LLM queries
def test_add_research_topic_annotations_to_workbook(tmp_path, use_mock, mocker):
    """Test add_research_topic_annotations_to_workbook"""

    # Parameterize the test
    workbook_path = "tests/edi.3.9_annotation_workbook.tsv"
    output_path = str(tmp_path) + "edi.3.9_annotation_workbook.tsv"

    # The workbook shouldn't have any annotations yet
    wb = load_workbook(workbook_path)
    assert not has_annotations(wb)

    # The workbook has annotations after calling the function
    if use_mock:
        mocker.patch(
            "spinneret.annotator.get_ontogpt_annotation",
            return_value=[{"label": "a label", "uri": "a uri"}],
        )
    wb = add_research_topic_annotations_to_workbook(
        workbook=workbook_path,
        eml=get_example_eml_dir() + "/" + "edi.3.9.xml",
        output_path=output_path,
        local_model="llama3.2",
        return_ungrounded=True,  # ensures we get at least one annotation back
    )
    assert has_annotations(wb)

    # Overwriting changes the annotations. Note, we can't test this with real
    # requests because we'll expect the same results as the first call.
    if use_mock:
        mocker.patch(  # an arbitrary response to check for
            "spinneret.annotator.get_ontogpt_annotation",
            return_value=[{"label": "a different label", "uri": "a different uri"}],
        )
    wb = add_research_topic_annotations_to_workbook(
        workbook=output_path,  # the output from the first call
        eml=get_example_eml_dir() + "/" + "edi.3.9.xml",
        output_path=output_path,
        local_model="llama3.2",
        return_ungrounded=True,  # ensures we get at least one annotation back
        overwrite=True,
    )
    assert wb["object"].str.contains("a different label").any()
    assert wb["object_id"].str.contains("a different uri").any()

    # Original annotations are gone
    assert not wb["object"].str.contains("a label").any()
    assert not wb["object_id"].str.contains("a uri").any()


@pytest.mark.parametrize("use_mock", [True])  # False tests with real local LLM queries
def test_add_methods_annotations_to_workbook(tmp_path, use_mock, mocker):
    """Test add_methods_annotations_to_workbook"""

    # Parameterize the test
    workbook_path = "tests/edi.3.9_annotation_workbook.tsv"
    output_path = str(tmp_path) + "edi.3.9_annotation_workbook.tsv"

    # The workbook shouldn't have any annotations yet
    wb = load_workbook(workbook_path)
    assert not has_annotations(wb)

    # The workbook has annotations after calling the function
    if use_mock:
        mocker.patch(
            "spinneret.annotator.get_ontogpt_annotation",
            return_value=[{"label": "a label", "uri": "a uri"}],
        )
    wb = add_methods_annotations_to_workbook(
        workbook=workbook_path,
        eml=get_example_eml_dir() + "/" + "edi.3.9.xml",
        output_path=output_path,
        local_model="llama3.2",
        return_ungrounded=True,  # ensures we get at least one annotation back
    )
    assert has_annotations(wb)

    # Overwriting changes the annotations. Note, we can't test this with real
    # requests because we'll expect the same results as the first call.
    if use_mock:
        mocker.patch(  # an arbitrary response to check for
            "spinneret.annotator.get_ontogpt_annotation",
            return_value=[{"label": "a different label", "uri": "a different uri"}],
        )
    wb = add_methods_annotations_to_workbook(
        workbook=output_path,  # the output from the first call
        eml=get_example_eml_dir() + "/" + "edi.3.9.xml",
        output_path=output_path,
        local_model="llama3.2",
        return_ungrounded=True,  # ensures we get at least one annotation back
        overwrite=True,
    )
    assert wb["object"].str.contains("a different label").any()
    assert wb["object_id"].str.contains("a different uri").any()

    # Original annotations are gone
    assert not wb["object"].str.contains("a label").any()
    assert not wb["object_id"].str.contains("a uri").any()
