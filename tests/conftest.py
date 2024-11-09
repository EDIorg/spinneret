"""Configure the test suite"""

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
