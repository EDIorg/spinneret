"""The benchmark module"""

import os
from typing import Union
import time
from collections import OrderedDict
import tempfile
import tracemalloc
from json import load
from contextlib import contextmanager
from daiquiri import getLogger
import pandas as pd
from spinneret.utilities import load_workbook, compress_uri
from spinneret.workbook import delete_duplicate_annotations


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

            standard = load_workbook(standard_path)
            test = load_workbook(test_path)

            # Prepare the data for comparison
            standard = clean_workbook(standard)
            test = clean_workbook(test)
            standard = group_object_ids(standard)
            test = group_object_ids(test)
            standard = compress_object_ids(standard)
            test = compress_object_ids(test)

            for key, standard_set in standard.items():
                if key not in test:
                    continue
                test_set = test[key]

                scores = get_termset_similarity(standard_set, test_set)
                if scores is None:
                    continue

                # Parse the scores and add them to the results
                r = OrderedDict()
                r["standard_dir"] = standard_dir
                r["test_dir"] = test_dir
                r["standard_file"] = standard_file
                r["predicate_value"] = key[0]
                r["element_xpath_value"] = key[1]
                r["standard_set"] = standard_set
                r["test_set"] = test_set
                r.update(scores)
                res.append(r)

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
    res = default_similarity_scores()  # a default ensures consistent returns

    # Clean the input sets in preparation for similarity scoring
    set1 = [term for term in set1 if term is not None]  # can't compare None
    set2 = [term for term in set2 if term is not None]
    set1 = delete_terms_from_unsupported_ontologies(set1)
    set2 = delete_terms_from_unsupported_ontologies(set2)

    if not set1 or not set2:  # can't calculate similarity of empty sets
        logger.info("Cannot calculate similarity for empty sets")
        return res

    db = get_shared_ontology(set1, set2)
    if db is None:  # can't compare terms from different ontologies
        return res

    # Write output file to a temporary location to be read back in later. We
    # do this because the output cannot be returned as an object.
    with tempfile.TemporaryDirectory() as temp_dir:
        output_file = os.path.join(temp_dir, "output.json")

        # Construct and run the termset-similarity command
        cmd = f"runoak -i {db} termset-similarity -o {output_file} -O json {' '.join(set1)} @ {' '.join(set2)}"
        try:
            os.system(cmd)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(f"Error running termset-similarity command: {e}")
            return res

        # Read and parse the similarity scores
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                scores = load(f)
        except FileNotFoundError as e:
            logger.error(f"Error reading termset-similarity output file: {e}")
            return res
        res = parse_similarity_scores(scores)
        return res


def default_similarity_scores() -> dict:
    """
    :return: A dictionary containing default similarity scores. Values are set
        following `oaklib` conventions.
    """
    res = OrderedDict()
    res["average_score"] = 0.0
    res["best_score"] = 0.0
    res["average_standard_information_content"] = pd.NA
    res["best_standard_information_content"] = pd.NA
    res["average_test_information_content"] = pd.NA
    res["best_test_information_content"] = pd.NA
    return res


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

    # Remove duplicate annotations, so we don't inflate the similarity scores
    # by comparing the same object multiple times.
    workbook = delete_duplicate_annotations(workbook)

    return workbook


def group_object_ids(workbook: pd.DataFrame) -> dict:
    """
    Group object_id values by predicate and element_xpath, i.e. the context
    of the object_id values that we are comparing.

    :param workbook: The workbook to apply the grouping to.
    :return: The grouped workbook as a dictionary, where the keys are tuples
        of the workbook predicate and element_xpath values, and the dictionary
        values are lists of object_id values.
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


def compress_object_ids(object_id_groups: dict) -> dict:
    """
    Convert object_ids to CURIEs for comparison.

    :param object_id_groups: The return value from `group_object_ids`.
    :return: The object_id_groups dictionary with object_ids converted to
        CURIEs.
    """
    for key, data in object_id_groups.items():
        object_id_groups[key] = [compress_uri(d) if d else None for d in data]
    return object_id_groups


def parse_similarity_scores(scores: list) -> dict:
    """
    Parse similarity scores from the output of the `oaklib` termset-similarity
    command into the format expected by the benchmarking function.

    :param scores: The output of the `oaklib` termset-similarity command.
    :return: A dictionary containing the parsed similarity scores.
    """
    res = default_similarity_scores()
    res["average_score"] = scores[0].get("average_score")
    res["best_score"] = scores[0].get("best_score")

    # Calculate the average and best information content scores
    for key in scores[0].keys():

        # Calculate for the subject (i.e. the "standard")
        if key == "subject_best_matches":
            ic_res = []
            for item in scores[0][key]:
                ic = scores[0][key][item]["similarity"][
                    "subject_information_content"]
                ic_res.append(ic)
            res["average_standard_information_content"] = sum(ic_res) / len(
                ic_res)
            res["best_standard_information_content"] = max(ic_res)

        # Calculate for the object (i.e. the "test")
        if key == "object_best_matches":
            ic_res = []
            for item in scores[0][key]:
                ic = scores[0][key][item]["similarity"][
                    "object_information_content"]
                ic_res.append(ic)
            res["average_test_information_content"] = sum(ic_res) / len(
                ic_res)
            res["best_test_information_content"] = max(ic_res)

        # TODO add jaccard_similarity average and best scores. Only need to do
        # this to the subject_best_matches because the object_best_matches
        # will be the same

        # TODO add phenodigm_score average and best scores. Only need to do
        # this to the subject_best_matches because the object_best_matches
        # will be the same

    return res


def delete_terms_from_unsupported_ontologies(set: list) -> list:
    """
    Similarity scoring works for some ontologies and not others, so remove
    terms that are not from supported ontologies. Supported ontologies are
    hard-coded in this function.

    :param set: List of CURIEs.
    :return: List of CURIEs from supported ontologies.
    """
    supported_ontologies = ["ENVO", "ECSO", "ENVTHES"]
    res = [
        term
        for term in set
        if any([term.startswith(ontology + ":") for ontology in
                supported_ontologies])
    ]
    return res


def get_shared_ontology(set1: list, set2: list) -> Union[str, None]:
    """
    Get the ontology shared between sets based on the most frequently occurring
    CURIE prefix in the input sets. Ontology support is hard-coded in this
    function.

    :param set1: List of CURIEs for the first set of terms.
    :param set2: List of CURIEs for the second set of terms.
    :return: The shared ontology. This value is returned as a string conforming
        to the `oaklib` conventions for specifying the ontology database input
        to the termset-similarity function. If no shared ontology is found,
        None is returned.
    """

    prefixes1 = [term.split(":")[0] for term in set1]
    prefixes2 = [term.split(":")[0] for term in set2]

    # Get the most common prefix in the intersection of the two sets
    intersection = set(prefixes1) & set(prefixes2)
    counts = {prefix: prefixes1.count(prefix) for prefix in intersection}
    if len(intersection) == 0:
        logger.info("Cannot find a common ontology for similarity scoring")
        return None
    prefix = max(counts, key=counts.get)

    # Map the prefix to the ontology database
    if prefix == "ENVO":
        db = "sqlite:obo:envo"
    elif prefix == "ECSO":
        db = "bioportal:ecso"
    elif prefix == "ENVTHES":
        db = "bioportal:envthes"
    else:
        logger.info(f"Ontology not supported: {prefix}")
        return None

    return db
