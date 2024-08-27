"""Test annotator code"""

import os
import pytest
from spinneret.annotator import get_bioportal_annotation
from spinneret.utilities import load_configuration


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
