"""Test graph code"""

from os import listdir
import importlib
import spinneret.graph


def test_combine_jsonld_files():
    """Test combine_jsonld_files"""
    data_dir = str(importlib.resources.files("spinneret.data")) + "/jsonld"
    files = [data_dir + "/" + f for f in listdir(data_dir)]
    res = spinneret.graph.combine_jsonld_files(files)
    assert res is not None
    assert len(res) > 0
