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
    with open(score_file, "r", encoding="utf-8") as file:
        return load(file)


@pytest.fixture(name="termset_similarity_score_processed")
def termset_similarity_score_processed():
    """Return a fixture for processed termset similarity scores returned by
    the get_termset_similarity function."""
    score_file = "tests/data/benchmark/termset_similarity_score_processed.json"
    with open(score_file, "r", encoding="utf-8") as file:
        return load(file)


@pytest.fixture(name="termset_similarity_score_fields")
def termset_similarity_score_fields():
    """Return a fixture for the fields expected in the termset similarity
    scores"""
    return [
        "average_score",
        "best_score",
        "average_jaccard_similarity",
        "best_jaccard_similarity",
        "average_phenodigm_score",
        "best_phenodigm_score",
        "average_standard_information_content",
        "best_standard_information_content",
        "average_test_information_content",
        "best_test_information_content",
    ]
