"""Test graph code"""

from os import listdir
import importlib
from spinneret.graph import create_graph


def test_create_graph():
    """Test create_graph"""

    # Load_metadata
    data_dir = str(importlib.resources.files("spinneret.data")) + "/jsonld"
    metadata_files = [data_dir + "/" + f for f in listdir(data_dir)]
    res = create_graph(metadata_files=metadata_files)
    assert res is not None
    assert len(res) == 650  # based on current metadata files

    # Load_vocabularies
    data_dir = "tests/data/vocab"
    vocabulary_files = [data_dir + "/" + f for f in listdir(data_dir)]
    res = create_graph(vocabulary_files=vocabulary_files)
    assert res is not None
    assert len(res) == 18  # based on current vocabulary files

    # Load both metadata and vocabularies
    res = create_graph(metadata_files=metadata_files, vocabulary_files=vocabulary_files)
    assert res is not None
    assert len(res) == 668  # based on current metadata and vocabulary files
