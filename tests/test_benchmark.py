"""Test benchmark code"""

import logging
import daiquiri
import pandas as pd
import pytest

from spinneret.benchmark import (
    monitor,
    benchmark_against_standard,
    get_termset_similarity,
    default_similarity_scores,
    clean_workbook,
    group_object_ids,
    compress_object_ids,
    parse_similarity_scores,
    delete_terms_from_unsupported_ontologies,
    get_shared_ontology,
)
from spinneret.utilities import is_url


def test_monitor(tmp_path):
    """Test the monitor context manager"""

    def example_function():  # to call with monitor
        return 1 + 1

    log_file = tmp_path / "test.log"  # set up daiquiri logger
    daiquiri.setup(
        level=logging.INFO,
        outputs=(
            daiquiri.output.File(log_file),
            "stdout",
        ),
    )

    with monitor("example_function"):  # test with monitor context manager
        example_function()

    with open(log_file, "r", encoding="utf-8") as file:
        log = file.read()
    assert "Starting function 'example_function'" in log
    assert "Function 'example_function' completed in" in log
    assert "Memory usage: Current=" in log


@pytest.mark.parametrize("use_mock", [True])  # False calculates similarity scores
def test_benchmark_against_standard(
    mocker,
    use_mock,
    termset_similarity_score_fields,
    termset_similarity_score_processed,
):
    """Test the benchmark_against_standard function"""

    if use_mock:
        mocker.patch(
            "spinneret.benchmark.get_termset_similarity",
            return_value=termset_similarity_score_processed,
        )

    res = benchmark_against_standard(
        standard_dir="tests/data/benchmark/standard",
        test_dirs=["tests/data/benchmark/test_a", "tests/data/benchmark/test_b"],
    )
    assert (
        res.columns.tolist()
        == [
            "standard_dir",
            "test_dir",
            "standard_file",
            "predicate_value",
            "element_xpath_value",
            "standard_set",
            "test_set",
        ]
        + termset_similarity_score_fields
    )


def test_get_termset_similarity(termset_similarity_score_fields):
    """Test the get_termset_similarity function"""

    # Get similarity scores for two sets of terms that are closely related.
    r = get_termset_similarity(
        set1={"ENVO:01000252"},  # freshwater lake biome
        set2={"ENVO:01000253"},  # freshwater river biome
    )
    assert isinstance(r, dict)
    assert r.keys() == set(termset_similarity_score_fields)
    for _, v in r.items():
        assert isinstance(v, float)

    # We expect lower similarity scores when we change one of the term sets to
    # a less related set of terms.
    r2 = get_termset_similarity(
        set1={"ENVO:01000252"},  # freshwater lake biome
        set2={"ENVO:01000182"},  # temperate desert biome
    )
    assert r2["average_score"] < r["average_score"]
    assert r2["best_score"] < r["best_score"]


def test_get_termset_similarity_with_empty_input_sets():
    """Test the get_termset_similarity function with empty input sets. The
    function should return default score values."""

    # Set 1 is empty
    r = get_termset_similarity(set1=[], set2=["ENVO:01000253"])
    assert r == default_similarity_scores()

    # Set 2 is empty
    r = get_termset_similarity(set1=["ENVO:01000252"], set2=[])
    assert r == default_similarity_scores()

    # Both sets are empty
    r = get_termset_similarity(set1=[], set2=[])
    assert r == default_similarity_scores()


def test_default_similarity_scores(termset_similarity_score_fields):
    """Test the default similarity scores return expected fields and values"""

    r = default_similarity_scores()
    assert isinstance(r, dict)
    assert set(r.keys()) == set(termset_similarity_score_fields)
    for k, v in r.items():
        if k in ["average_score", "best_score"]:
            assert v == 0.0
        else:
            assert isinstance(v, type(pd.NA))


def test_clean_workbook(annotated_workbook):
    """Test the clean_workbook function"""
    wb = annotated_workbook

    # Dirty-up the workbook by adding NA values and ungrounded terms in the
    # "object_id" column
    wb.loc[0, "object_id"] = pd.NA
    assert wb["object_id"].isna().any()
    wb.loc[1, "object_id"] = "AUTO:1234"
    assert wb["object_id"].str.startswith("AUTO:").any()

    # After cleaning, the NA values and ungrounded terms will be gone
    wb_cleaned = clean_workbook(wb)
    assert not wb_cleaned["object_id"].isna().any()
    assert not wb_cleaned["object_id"].str.startswith("AUTO:").any()


def test_group_object_ids(annotated_workbook):
    """Test the group_object_ids function"""
    wb = annotated_workbook

    # Group the workbook by predicate and element_xpath
    grouped = group_object_ids(wb)
    assert isinstance(grouped, dict)

    # The keys are tuples composed of the predicate and element_xpath values
    assert isinstance(list(grouped.keys())[0], tuple)

    # Each value is a list of object_ids corresponding to the predicate and
    # element_xpath grouping
    assert isinstance(list(grouped.values())[0], list)
    assert isinstance(list(grouped.values())[1][0], str)
    assert is_url(list(grouped.values())[1][0])


def test_compress_object_ids(annotated_workbook):
    """The test_compress_object_ids function"""

    # Create grouped dictionary for testing
    wb = annotated_workbook
    grouped = group_object_ids(wb)

    # Grouped dictionary values are URI strings before compression
    for _, values in grouped.items():
        for v in values:
            if not v:  # skip empty lists
                continue
            assert is_url(v)

    # After compression, the values are lists of CURIES
    compressed = compress_object_ids(grouped)
    for _, values in compressed.items():
        for v in values:
            if not v:  # skip empty lists
                continue
            assert not is_url(v)
            assert len(v.split(":")) == 2


def test_parse_similarity_scores(
    termset_similarity_score_raw, termset_similarity_score_fields
):
    """Test the parse_similarity_scores function"""

    # The parsed result should be a dictionary with the expected keys
    r = parse_similarity_scores(termset_similarity_score_raw)
    assert isinstance(r, dict)
    assert set(r.keys()) == set(termset_similarity_score_fields)


def test_delete_terms_from_unsupported_ontologies():
    """Test the delete_terms_from_unsupported_ontologies function"""

    # Terms (CURIES) from supported ontologies are retained
    supported_terms = ["ENVO:01000252", "ECSO:01000253", "ENVTHES:0000002"]
    r = delete_terms_from_unsupported_ontologies(supported_terms)
    assert r == supported_terms

    # Terms from unsupported ontologies are removed
    mixed_term_list = supported_terms + ["AUTO:1234", "FOO:5678"]
    r = delete_terms_from_unsupported_ontologies(mixed_term_list)
    assert r == supported_terms


def test_get_shared_ontology():
    """Test the get_shared_ontology function"""

    # An ontology is returned when the two sets share the same ontology
    set1 = ["ENVO:01000252", "ENVO:01000253"]
    set2 = ["ENVO:01000252"]
    db = get_shared_ontology(set1, set2)
    assert db == "sqlite:obo:envo"

    set1 = ["ENVO:01000252", "ECSO:01000253"]
    set2 = ["ENVO:01000252"]
    db = get_shared_ontology(set1, set2)
    assert db == "sqlite:obo:envo"

    # None is returned for unsupported ontologies
    set1 = ["ECSO:01000253"]
    set2 = ["ECSO:01000253"]
    db = get_shared_ontology(set1, set2)
    assert db is None

    # None is returned when the two sets do not share a common ontology
    set1 = ["ENVO:01000252", "ENVO:01000253"]
    set2 = ["ECSO:01000252"]
    db = get_shared_ontology(set1, set2)
    assert db is None

    # None is returned when one or both sets are empty
    set1 = []
    set2 = ["ENVO:01000252"]
    db = get_shared_ontology(set1, set2)
    assert db is None

    set1 = []
    set2 = []
    db = get_shared_ontology(set1, set2)
    assert db is None
