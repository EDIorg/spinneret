"""Test graph code"""

from os import listdir
import importlib
from spinneret.graph import load_metadata, load_vocabularies, load_graph


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


def test_load_graph():
    """Test load_graph"""

    # Load_metadata
    data_dir = str(importlib.resources.files("spinneret.data")) + "/jsonld"
    metadata_files = [data_dir + "/" + f for f in listdir(data_dir)]
    res = load_graph(metadata_files=metadata_files)
    assert res is not None
    assert len(res) == 650  # based on current metadata files

    # Load_vocabularies
    data_dir = "tests/data/vocab"
    vocabulary_files = [data_dir + "/" + f for f in listdir(data_dir)]
    res = load_graph(vocabulary_files=vocabulary_files)
    assert res is not None
    assert len(res) == 18  # based on current vocabulary files

    # Load both metadata and vocabularies
    res = load_graph(metadata_files=metadata_files, vocabulary_files=vocabulary_files)
    assert res is not None
    assert len(res) == 668  # based on current metadata and vocabulary files
