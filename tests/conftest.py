"""Configure the test suite"""

from json import load
import pytest
from spinneret.utilities import load_workbook


@pytest.fixture(name="get_annotation_fixture")
def get_annotation_fixture():
    """Return a fixture for annotators."""
    return [
        {"label": "a label", "uri": "a uri"},
        {"label": "another label", "uri": "another uri"},
    ]


@pytest.fixture(name="annotated_workbook")
def annotated_workbook():
    """Return a fixture for an annotated workbook"""
    wb = load_workbook("tests/edi.3.9_annotation_workbook_annotated.tsv")
    return wb


@pytest.fixture(name="termset_similarity_score_raw")
def termset_similarity_score_raw():
    """Return a fixture for raw termset similarity scores returned by the
    `runoak -i {db} termset-similarity` command."""
    score_file = "tests/data/benchmark/termset_similarity_score_raw.json"
    with open(score_file, "r") as file:
        return load(file)


@pytest.fixture(name="termset_similarity_score_processed")
def termset_similarity_score_processed():
    """Return a fixture for processed termset similarity scores returned by
    the get_termset_similarity function."""
    # TODO update this file with phenodigm_score and jaccard_similarity
    score_file = "tests/data/benchmark/termset_similarity_score_processed.json"
    with open(score_file, "r") as file:
        return load(file)
