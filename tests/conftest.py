"""Configure the test suite"""

import pytest


@pytest.fixture(name="get_annotation_fixture")
def get_annotation_fixture():
    """Return a fixture for annotators."""
    return [
        {"label": "a label", "uri": "a uri"},
        {"label": "another label", "uri": "another uri"},
    ]
