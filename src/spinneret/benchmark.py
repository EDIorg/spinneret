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


def benchmark_against_standard(standard_dir: str, test_dirs: list) -> pd.DataFrame:
    """
    Benchmarks the performance of test data against a standard.

    :param standard_dir: Directory containing the standard annotated workbook
        files.
    :param test_dirs: List of directories containing the test annotated
        workbook files. Each directory represents a different test condition.
    :return: A pandas DataFrame containing the benchmark results. Comparisons
        are made between the standard and test data for each predicate and
        element_xpath combination. The DataFrame contains the following columns:

        - standard_dir: The directory containing the standard annotated
          workbook files.
        - test_dir: The directory containing the test annotated workbook files.
        - standard_file: The name of the standard annotated workbook file.
        - predicate_value: The value of the predicate column.
        - element_xpath_value: The value of the element_xpath column.
        - standard_set: The set of object_ids from the standard data.
        - test_set: The set of object_ids from the test data.
        - average_termset_similarity: The average similarity score between the
          standard and test sets.
        - best_termset_similarity: The best similarity score between the
          standard and test sets.
        - max_standard_information_content: The maximum information content of
          the standard set.
        - average_standard_information_content: The average information content
          of the standard set.
        - max_test_information_content: The maximum information content of the
          test set.
        - average_test_information_content: The average information content of
          the test set.
    """

    res = []

    for standard_file in os.listdir(standard_dir):
        if not standard_file.endswith(".tsv"):  # we are expecting tsv files
            continue
        standard_path = os.path.join(standard_dir, standard_file)

        for test_dir in test_dirs:
            test_path = os.path.join(test_dir, standard_file)
            if not os.path.exists(test_path):  # we need a matching test file
                continue

            standard_df = load_workbook(standard_path)
            test_df = load_workbook(test_path)

            # Prepare the data for comparison
            standard_df = clean_workbook(standard_df)
            test_df = clean_workbook(test_df)
            standard_data = group_object_ids(standard_df)
            test_data = group_object_ids(test_df)

            # TODO apply this within an xpath+predicate group?
            # Uniqueify the "object_id" column, otherwise we could be comparing
            # the same object multiple times leading to inflated scores
            # workbook = workbook.drop_duplicates(subset=["object_id"])

            # TODO: implement convert_object_id_to_curie
            # Convert the object_ids to CURIEs for the comparison function
            converter: Converter = load_converter(["obo", "bioportal"])
            for key, data in standard_data.items():
                standard_data[key] = [converter.compress(d) for d in data]
            for key, data in test_data.items():
                test_data[key] = [converter.compress(d) for d in data]

            for key, standard_set in standard_data.items():

                # TODO continue if not in test_data (to have fewer nested blocks)
                if key in test_data:
                    test_set = test_data[key]

                    score = get_termset_similarity(standard_set, test_set)  # TODO rename?
                    if score is None:
                        continue

                    res.append(
                        {
                            "standard_dir": standard_dir,
                            "test_dir": test_dir,
                            "standard_file": standard_file,
                            "predicate_value": key[0],
                            "element_xpath_value": key[1],
                            "standard_set": standard_set,
                            "test_set": test_set,
                            "average_termset_similarity": score.get("average_score", pd.NA),
                            "best_termset_similarity": score.get("best_score", pd.NA),
                            "max_standard_information_content": score.get("max_subject_information_content", pd.NA),
                            "average_standard_information_content": score.get("average_subject_information_content", pd.NA),
                            "max_test_information_content": score.get("max_object_information_content", pd.NA),
                            "average_test_information_content": score.get("average_object_information_content", pd.NA),
                        }
                    )
    return pd.DataFrame(res)


def get_termset_similarity(set1: list, set2: list) -> dict:
    """
    Calculate the similarity between two sets of terms.

    :param set1: List of CURIEs for the first set of terms.
    :param set2: List of CURIEs for the second set of terms.
    :return: A dictionary containing termset similarity and information content
        scores. Default values, defined in
        `benchmark.default_similarity_scores` are returned if the similarity
        scores cannot be calculated or if an error occurs. For more information
        on scoring, see the `oaklib` documentation: https://incatools.github.io/ontology-access-kit/guide/similarity.html.
    :notes: This is a simple wrapper around the `oaklib` termset-similarity
        function (https://incatools.github.io/ontology-access-kit/cli.html#runoak-termset-similarity).
    """
    res = default_similarity_scores()

    # Clean up the input to prevent errors
    # Remove None values from set1 and set2 to prevent errors
    set1 = [term for term in set1 if term is not None]
    set2 = [term for term in set2 if term is not None]

    # TODO: Implement delete_terms_from_unsupported_ontologies
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

    # If either set is empty then we can't calculate similarity
    if not set1 or not set2:
        logger.info("Cannot calculate similarity for empty sets")
        return res

    # TODO: Implement get_ontology_for_similarity_scoring
    # TODO need to think through the logic of this one, possibly raise to a note or a separate function with it's own documentation
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
        print("Cannot calculate similarity between terms from different ontologies")  # TODO Convert to logger
        return res  # TODO return None, and in the outter function return res if None
    # Load the ontology of the most frequently occuring CURIE prefix in the set
    if prefix == "ENVO":
        db = "sqlite:obo:envo"
    elif prefix == "ECSO":
        db = "sqlite:obo:ecso"  # TODO double check this
    elif prefix == "ENVTHES":
        db = "sqlite:obo:envthes"  # TODO double check this
    else:
        print(f"Ontology not supported: {prefix}") # TODO Convert to logger
        return res  # TODO return None, and in the outter function return res if None

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
            return res

        # Parse the results
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                r = load(f)
        except FileNotFoundError as e:
            logger.error(f"Error reading termset-similarity output file: {e}")
            return res

        # TODO: Implement get_termset_similarity_scores
        # Get termset similarity scores
        res["average_score"] = r[0].get("average_score")
        res["best_score"] = r[0].get("best_score")
        # Iterate over keys in r
        for key in r[0].keys():
            if key == "subject_best_matches":
                ic_res = []
                for item in r[0][key]:
                    ic = r[0][key][item]["similarity"]["subject_information_content"]
                    ic_res.append(ic)
                res["max_subject_information_content"] = max(ic_res)
                res["average_subject_information_content"] = sum(ic_res) / len(ic_res)
            if key == "object_best_matches":
                ic_res = []
                for item in r[0][key]:
                    ic = r[0][key][item]["similarity"]["object_information_content"]
                    ic_res.append(ic)
                res["max_object_information_content"] = max(ic_res)
                res["average_object_information_content"] = sum(ic_res) / len(ic_res)
        return res


def default_similarity_scores() -> dict:
    """
    :return: A dictionary containing default similarity scores. Values are set
        following `oaklib` conventions.
    """
    return {
        "average_score": 0.0,
        "best_score": 0.0,
        "max_subject_information_content": pd.NA,
        "average_subject_information_content": pd.NA,
        "max_object_information_content": pd.NA,
        "average_object_information_content": pd.NA,
    }


def clean_workbook(workbook: pd.DataFrame) -> pd.DataFrame:
    """
    Clean a workbook for benchmarking.

    :param workbook: The workbook to clean.
    :return: The cleaned workbook.
    """
    # Remove rows where the "object_id" is NaN. This is necessary because
    # the termset similarity function cannot handle NaN values.
    workbook = workbook.dropna(subset=["object_id"])

    # Remove rows where the "object_id" starts with "AUTO:", these terms are
    # not grounded to any ontology and therefore cannot be compared.
    workbook = workbook[~workbook["object_id"].str.startswith("AUTO:")]

    return workbook


def group_object_ids(workbook: pd.DataFrame) -> dict:
    """
    Group object_id values by predicate and element_xpath, i.e. the context
    of the object_id values that we are comparing.

    :param workbook: The workbook to apply the grouping to.
    :return: The grouped workbook as a series, where the index is a tuple
        containing the predicate and element_xpath values, and the values are
        lists of object_id values.
    """
    # list_object_id_for_predicate_and_element_xpath
    # Group data by predicate and element_xpath columns
    series = workbook.groupby(
        ["predicate", "element_xpath"]
    ).apply(lambda x: x.to_dict("records"), include_groups=False)

    # Only include the "object_id" values, these are what we want to compare
    res = {
        key: [d["object_id"] for d in data]
        for key, data in series.items()
    }
    return res


if __name__ == "__main__":

    cmd = "runoak -i sqlite:obo:envo termset-similarity -o /Users/csmith/Data/ontogpt_testing/similarity.json -O json ENVO:01000252 ENVO:01000548 @ ENVO:01000317"
    os.system(cmd)
