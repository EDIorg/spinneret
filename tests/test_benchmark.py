"""Test benchmark code"""

import logging
import daiquiri
import pandas as pd
from spinneret.benchmark import (
    monitor,
    benchmark_against_standard,
    get_termset_similarity,
    default_similarity_scores,
    clean_workbook,
    group_object_ids,
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


def test_benchmark_against_standard():
    """Test the benchmark_against_standard function"""

    res = benchmark_against_standard(
        standard_dir="tests/data/benchmark/standard",
        test_dirs=["tests/data/benchmark/test_a",
                   "tests/data/benchmark/test_b"],
    )

    assert res.shape == (8, 13)
    assert res.columns.tolist() == ['standard_dir', 'test_dir',
                                    'standard_file', 'predicate_value',
                                    'element_xpath_value', 'standard_set',
                                    'test_set', 'average_termset_similarity',
                                    'best_termset_similarity',
                                    'max_standard_information_content',
                                    'average_standard_information_content',
                                    'max_test_information_content',
                                    'average_test_information_content']


def test_get_termset_similarity():
    """Test the get_termset_similarity function"""

    # TODO mock network calls

    # Get similarity scores for two sets of terms that are closely related.
    r = get_termset_similarity(
        set1={"ENVO:01000252"},  # freshwater lake biome
        set2={"ENVO:01000253"},  # freshwater river biome
    )
    assert isinstance(r, dict)
    assert set(r.keys()) == {"average_score", "best_score",
                             "max_subject_information_content",
                             "max_object_information_content",
                             "average_subject_information_content",
                             "average_object_information_content"}
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


def test_default_similarity_scores():
    """Test the default similarity scores return expected fields and values"""

    r = default_similarity_scores()
    assert isinstance(r, dict)
    assert set(r.keys()) == {"average_score", "best_score",
                             "max_subject_information_content",
                             "max_object_information_content",
                             "average_subject_information_content",
                             "average_object_information_content"}
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
