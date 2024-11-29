"""Test benchmark code"""

import logging
import daiquiri
from spinneret.benchmark import (
    monitor,
    benchmark_against_standard,
    get_termset_similarity,
)


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

    def comparison_function(standard, test):
        return 1

    result = benchmark_against_standard(
        standard_dir="tests/data/benchmark/standard",
        test_dirs=["tests/data/benchmark/test_a", "tests/data/benchmark/test_b"],
        comparison_function=comparison_function,
        predicate_column="predicate",
        element_xpath_column="element_xpath",
    )

    # TODO remove me
    from spinneret.utilities import write_workbook

    write_workbook(
        result,
        "/Users/csmith/Code/spinneret_EDIorg/spinneret/tests/data/benchmark/standard/benchmark_results.tsv",
    )

    assert result.shape == (2, 8)
    assert result.columns.tolist() == [
        "standard_dir",
        "test_dir",
        "standard_file",
        "predicate_value",
        "element_xpath_value",
        "standard_set",
        "test_set",
        "score",
    ]
    assert result["score"].tolist() == [1, 1]
    assert result["standard_dir"].tolist() == [
        "tests/data/standard",
        "tests/data/standard",
    ]
    assert result["test_dir"].tolist() == ["tests/data/test", "tests/data/test"]
    assert result["standard_file"].tolist() == ["standard.xml", "standard.xml"]
    assert result["predicate_value"].tolist() == ["predicate1", "predicate2"]
    assert result["element_xpath_value"].tolist() == [
        "element_xpath1",
        "element_xpath2",
    ]
    assert result["standard_set"].tolist() == ["standard_set1", "standard_set2"]
    assert result["test_set"].tolist() == ["test_set1", "test_set2"]


def test_get_termset_similarity():
    """Test the get_termset_similarity function"""

    # TODO mock network calls

    # Get similarity scores for two sets of terms that are closely related.
    r = get_termset_similarity(
        set1={"ENVO:01000252"},  # freshwater lake biome
        set2={"ENVO:01000253"},  # freshwater river biome
    )
    assert isinstance(r, dict)
    assert set(r.keys()) == {"average_score", "best_score"}
    assert isinstance(r["average_score"], float)
    assert isinstance(r["best_score"], float)

    # We expect lower similarity scores when we change one of the term sets to
    # a less related set of terms.
    r2 = get_termset_similarity(
        set1={"ENVO:01000252"},  # freshwater lake biome
        set2={"ENVO:01000182"},  # temperate desert biome
    )
    assert r2["average_score"] < r["average_score"]
    assert r2["best_score"] < r["best_score"]
