"""Test graph code"""

from os import listdir
import importlib
from spinneret.graph import load_metadata, load_vocabularies


def test_combine_jsonld_files():
    """Test load_metadata"""
    data_dir = str(importlib.resources.files("spinneret.data")) + "/jsonld"
    files = [data_dir + "/" + f for f in listdir(data_dir)]
    res = load_metadata(files)
    assert res is not None
    assert len(res) > 0


def test_load_vocabularies():
    """Test load_vocabularies"""
    data_dir = "tests/data/vocab"
    files = [data_dir + "/" + f for f in listdir(data_dir)]
    res = load_vocabularies(files)
    assert res is not None
    assert len(res) > 0
