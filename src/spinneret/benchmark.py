"""The benchmark module"""

import os
import time
import tempfile
import tracemalloc
from json import load
from contextlib import contextmanager
from daiquiri import getLogger
import pandas as pd
from prefixmaps import load_converter
from curies import Converter
from spinneret.utilities import load_workbook


logger = getLogger(__name__)


@contextmanager
def monitor(name: str) -> None:
    """
    Context manager to monitor the duration and memory usage of a function
    using the `daiquiri` package logger.

    :param name: The name of the function being monitored.
    :return: None
    """
    start_time = time.time()
    tracemalloc.start()
    logger.info(f"Starting function '{name}'")
    try:
        yield  # The code inside the `with` block runs here
    except Exception as e:
        logger.error(f"Function '{name}' raised an exception: {e}")
        raise
    finally:
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        duration = time.time() - start_time
        logger.info(f"Function '{name}' completed in {duration:.4f} seconds")
        logger.info(
            f"Memory usage: Current={current / 1024:.2f} KB; Peak={peak / 1024:.2f} KB"
        )


def benchmark_against_standard(
    standard_dir, test_dirs, comparison_function, predicate_column, element_xpath_column
):
    """
    Benchmarks the performance of test data against a standard.

    Args:
        standard_dir: Directory containing the standard data files.
        test_dirs: List of directories containing test data.
        comparison_function: Function to compare two sets of data.
        predicate_column: Name of the column used to group data into sets.
        element_xpath_column: Name of the column used to further group data within sets.

    Returns:
        A pandas DataFrame with columns:
            - standard_dir
            - test_dir
            - standard_file
            - predicate_value
            - element_xpath_value
            - standard_set
            - test_set
            - score
    """

    results = []

    for standard_file in os.listdir(standard_dir):
        if not standard_file.endswith(".tsv"):  # we are expecting tsv files
            continue
        standard_path = os.path.join(standard_dir, standard_file)

        for test_dir in test_dirs:
            test_path = os.path.join(test_dir, standard_file)

            if not os.path.exists(test_path):
                continue  # Skip if test file doesn't exist

            standard_df = load_workbook(standard_path)
            test_df = load_workbook(test_path)

            # Remove rows where the "object_id" is NaN
            standard_df = standard_df.dropna(subset=["object_id"])
            test_df = test_df.dropna(subset=["object_id"])

            # Remove rows where the "object_id" starts with "AUTO:", these are
            # ungrounded terms that are not useful for comparison
            standard_df = standard_df[~standard_df["object_id"].str.startswith("AUTO:")]
            test_df = test_df[~test_df["object_id"].str.startswith("AUTO:")]

            # Uniqueify the "object_id" column, otherwise we could be comparing
            # the same object multiple times leading to inflated scores
            standard_df = standard_df.drop_duplicates(subset=["object_id"])
            test_df = test_df.drop_duplicates(subset=["object_id"])

            # Group data by predicate and element_xpath columns
            standard_data = standard_df.groupby(
                [predicate_column, element_xpath_column]
            ).apply(lambda x: x.to_dict("records"))
            test_data = test_df.groupby([predicate_column, element_xpath_column]).apply(
                lambda x: x.to_dict("records")
            )

            # Only include the "object_id" in the standard and test data, we
            # are only interested in comparing the sets of object_ids
            standard_data = {
                key: [d["object_id"] for d in data]
                for key, data in standard_data.items()
            }
            test_data = {
                key: [d["object_id"] for d in data] for key, data in test_data.items()
            }

            # Convert the object_ids to CURIEs for the comparison function
            converter: Converter = load_converter(["obo", "bioportal"])
            for key, data in standard_data.items():
                standard_data[key] = [converter.compress(d) for d in data]
            for key, data in test_data.items():
                test_data[key] = [converter.compress(d) for d in data]

            for key, standard_set in standard_data.items():
                if key in test_data:
                    test_set = test_data[key]

                    # TODO add other similarity scores?
                    score = get_termset_similarity(standard_set, test_set)

                    results.append(
                        {
                            "standard_dir": standard_dir,
                            "test_dir": test_dir,
                            "standard_file": standard_file,
                            "predicate_value": key[0],
                            "element_xpath_value": key[1],
                            "standard_set": standard_set,
                            "test_set": test_set,
                            "score": score,
                        }
                    )
    return pd.DataFrame(results)


def get_termset_similarity(set1: list, set2: list) -> dict:
    """
    Calculate the similarity between two sets of terms.

    :param set1: List of CURIEs for the first set of terms.
    :param set2: List of CURIEs for the second set of terms.
    :return: A dictionary containing the average and best similarity scores.
        Has keys 'average_score' and 'best_score'.
    """
    # Similarity scoring works for some ontologies and not others, so remove
    # terms that are not from supported ontologies
    supported_ontologies = ["ENVO", "ECSO", "ENVTHES"]
    set1 = [
        term
        for term in set1
        if any([term.startswith(ontology + ":") for ontology in supported_ontologies])
    ]
    set2 = [
        term
        for term in set2
        if any([term.startswith(ontology + ":") for ontology in supported_ontologies])
    ]

    # Get most frequently occuring CURIE prefix in set1 and set2
    # This is a simple heuristic to determine which ontology to load for the
    # similarity scoring
    prefix1 = os.path.commonprefix(set1)
    prefix2 = os.path.commonprefix(set2)
    prefix1 = prefix1.split(":")[0]
    prefix2 = prefix2.split(":")[0]
    # If the prefixes match then we can use that ontology for similarity scoring
    if prefix1 == prefix2:
        prefix = prefix1
    else:
        # If the prefixes don't match then we can't use similarity scoring
        print("Cannot calculate similarity between terms from different ontologies")
        return None

    # Load the ontology of the most frequently occuring CURIE prefix in the set
    if prefix == "ENVO":
        db = "sqlite:obo:envo"
    elif prefix == "ECSO":
        db = "sqlite:obo:ecso"  # TODO double check this
    elif prefix == "ENVTHES":
        db = "sqlite:obo:envthes"  # TODO double check this
    else:
        print(f"Ontology not supported: {prefix}")
        return None

    # Write output file to a temporary location. We do this because the output
    # cannot be returned as a value from the function, it must be written to a
    # file and then read back in.
    with tempfile.TemporaryDirectory() as temp_dir:
        output_file = os.path.join(temp_dir, "output.json")

        # Construct the command to run, then try to run it. Note, there is a
        # Python API for this but module import errors thrown within the
        # Pycharm IDE preclude efficient run/debug operations.
        cmd = f"runoak -i {db} termset-similarity -o {output_file} -O json {' '.join(set1)} @ {' '.join(set2)}"
        try:
            os.system(cmd)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(f"Error running termset-similarity command: {e}")
            return None

        # Parse the results
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                r = load(f)
        except FileNotFoundError as e:
            logger.error(f"Error reading termset-similarity output file: {e}")
            return None
        res = {
            "average_score": r[0].get("average_score"),
            "best_score": r[0].get("best_score"),
        }
        return res


if __name__ == "__main__":

    cmd = "runoak -i sqlite:obo:envo termset-similarity -o /Users/csmith/Data/ontogpt_testing/similarity.json -O json ENVO:01000252 ENVO:01000548 @ ENVO:01000317"
    os.system(cmd)
