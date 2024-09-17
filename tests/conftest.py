"""Configure the test suite"""

import pytest


@pytest.fixture(name="get_bioportal_annotation_fixture")
def get_bioportal_annotation_fixture():
    """Create a get_bioportal_annotation return value fixture for tests."""
    return [
        {"label": "a label", "uri": "a uri"},
        {"label": "another label", "uri": "another uri"},
    ]
