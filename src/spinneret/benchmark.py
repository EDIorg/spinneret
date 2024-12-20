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
import matplotlib.pyplot as plt
import numpy as np
from spinneret.utilities import load_workbook, compress_uri
from spinneret.workbook import delete_duplicate_annotations, delete_unannotated_rows


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
    Benchmarks the performance of test data against a standard. Currently
    supports select ontologies from the OBO Foundry.

    :param standard_dir: Directory containing the standard annotated workbook
        files.
    :param test_dirs: List of directories containing the test annotated
        workbook files. Each directory represents a different test condition.
    :return: A pandas DataFrame containing the benchmark results. Comparisons
        are made between the standard and test data for each predicate and
        element_xpath combination. The DataFrame contains the following
        columns:

        - standard_dir: The directory containing the standard annotated
          workbook files.
        - test_dir: The directory containing the test annotated workbook files.
        - standard_file: The name of the standard annotated workbook file.
        - predicate_value: The value of the predicate column.
        - element_xpath_value: The value of the element_xpath column.
        - standard_set: The set of object_ids from the standard data.
        - test_set: The set of object_ids from the test data.
        - average_score: The average termset similarity score between the
          standard and test sets.
        - best_score: The best termset similarity score between the standard
          and test sets.
        - average_jaccard_similarity: The average Jaccard similarity score
          between the standard and test sets.
        - best_jaccard_similarity: The best Jaccard similarity score between
          the standard and test sets.
        - average_phenodigm_score: The average Phenodigm score between the
          standard and test sets.
        - best_phenodigm_score: The best Phenodigm score between the standard
          and test sets.
        - average_standard_information_content: The average information content
          score of the standard set.
        - best_standard_information_content: The best information content
          score of the standard set.
        - average_test_information_content: The average information content
          score of the test set.
        - best_test_information_content: The best information content score of
          the test set.
    """
    res = []

    for standard_file in os.listdir(standard_dir):
        if not standard_file.endswith(".tsv"):  # we are expecting tsv files
            continue
        standard_path = os.path.join(standard_dir, standard_file)
        logger.info(f"Benchmarking against standard file: {standard_path}")

        for test_dir in test_dirs:
            test_path = os.path.join(test_dir, standard_file)
            logger.info(f"Comparing to test file: {test_path}")
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
        on scoring, see the `oaklib` documentation:
        https://incatools.github.io/ontology-access-kit/guide/similarity.html.
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
        cmd = (
            f"runoak -i {db} termset-similarity -o {output_file} -O json "
            f"{' '.join(set1)} @ {' '.join(set2)}"
        )
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
    res["average_jaccard_similarity"] = pd.NA
    res["best_jaccard_similarity"] = pd.NA
    res["average_phenodigm_score"] = pd.NA
    res["best_phenodigm_score"] = pd.NA
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
    series = workbook.groupby(["predicate", "element_xpath"]).apply(
        lambda x: x.to_dict("records"), include_groups=False
    )

    # Only include the "object_id" values, these are what we want to compare
    res = {key: [d["object_id"] for d in data] for key, data in series.items()}
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

    # Get the "termset similarity" scores
    res["average_score"] = scores[0].get("average_score")
    res["best_score"] = scores[0].get("best_score")

    # Get other similarity scores (i.e. information content, jaccard
    # similarity, phenodigm score)
    for key in scores[0].keys():

        # Information content scores
        if key == "subject_best_matches":  # for the subject (i.e. "standard")
            r = []
            for item in scores[0][key]:
                s = scores[0][key][item]["similarity"]["subject_information_content"]
                r.append(s)
            res["average_standard_information_content"] = sum(r) / len(r)
            res["best_standard_information_content"] = max(r)
        if key == "object_best_matches":  # for the object (i.e. the "test")
            r = []
            for item in scores[0][key]:
                s = scores[0][key][item]["similarity"]["object_information_content"]
                r.append(s)
            res["average_test_information_content"] = sum(r) / len(r)
            res["best_test_information_content"] = max(r)

        # Jaccard similarity scores. Note, we can get this information from
        # either the subject_best_matches or object_best_matches keys. Doing
        # both is redundant.
        if key == "subject_best_matches":
            r = []
            for item in scores[0][key]:
                s = scores[0][key][item]["similarity"]["jaccard_similarity"]
                r.append(s)
            res["average_jaccard_similarity"] = sum(r) / len(r)
            res["best_jaccard_similarity"] = max(r)

        # Phenodigm scores. Note, we can get this information from either the
        # subject_best_matches or object_best_matches keys. Doing both is
        # redundant.
        if key == "subject_best_matches":
            r = []
            for item in scores[0][key]:
                s = scores[0][key][item]["similarity"]["phenodigm_score"]
                r.append(s)
            res["average_phenodigm_score"] = sum(r) / len(r)
            res["best_phenodigm_score"] = max(r)

    return res


def delete_terms_from_unsupported_ontologies(curies: list) -> list:
    """
    Similarity scoring works for some ontologies and not others, so remove
    terms that are not from supported ontologies. Supported ontologies are
    hard-coded in this function.

    :param curies: List of CURIEs.
    :return: List of CURIEs from supported ontologies.
    """
    supported_ontologies = ["ENVO", "ECSO", "ENVTHES"]
    res = [
        term
        for term in curies
        if any(term.startswith(ontology + ":") for ontology in supported_ontologies)
    ]
    return res


def get_shared_ontology(set1: list, set2: list) -> Union[str, None]:
    """
    Get the most shared ontology of two sets based on the most frequently
    occurring CURIE prefix.

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
    else:
        logger.info(f"Ontology not supported: {prefix}")
        return None

    return db


def plot_grounding_rates(
    grounding_rates: dict, configuration: str, output_file: str = None
) -> None:
    """
    Plot the grounding rates of the test data.

    :param grounding_rates: The return value from the `get_grounding_rates`
        function.
    :param configuration: The configuration of OntoGPT that was used to
        generate the test data. This is typically the directory name of the
        test data.
    :param output_file: The path to save the plot to, as a PNG file.
    :return: None
    """

    # Reformating the grounding rates dictionary into a DataFrame for plotting
    df = pd.DataFrame(grounding_rates).T

    # Calculate percentages
    df_percent = df.div(df.sum(axis=1), axis=0) * 100

    # Add data labels to the bars
    plt.figure(figsize=(10, 6))
    bottom = [0] * len(df)
    for col in df_percent.columns:
        bars = plt.bar(df_percent.index, df_percent[col], bottom=bottom, label=col)
        for item in bars:
            height = item.get_height()
            if height > 5:  # Only add labels if the segment is large enough
                plt.text(
                    item.get_x() + item.get_width() / 2,
                    item.get_y() + height / 2,
                    f"{height:.1f}%",
                    ha="center",
                    va="center",
                    color="white",
                    fontsize=9,
                )
        bottom = [bottom[i] + df_percent[col][i] for i in range(len(bottom))]

    plt.ylabel("Percentage")
    title = f"OntoGPT Grounding Rates for Configuration '{configuration}'"
    plt.title(title)
    plt.xticks(rotation=-20)
    plt.legend(title="State")
    plt.tight_layout()
    if output_file:
        plt.savefig(output_file, dpi=300)
    plt.show()


def get_grounding_rates(test_dir: str) -> dict:
    """
    Get the OntoGPT grounding rates of the test data, by predicate.

    Predicates may have different grounding rates, due to differences in LLM
    prompting and the nature of the vocabularies/ontologies being grounded to.

    :param test_dir: Path to a directory containing the test annotated
        workbook files.
    :return: A nested set of dictionaries containing the grounding rates of the
        test data. The first level of dictionary keys are the predicates, and
        the values are a second dictionary with keys "grounded" and
        "ungrounded". The values of these keys are the number of grounded and
        ungrounded terms, respectively.
    """
    res = {
        "env_broad_scale": {"grounded": 0, "ungrounded": 0},
        "env_local_scale": {"grounded": 0, "ungrounded": 0},
        "contains process": {"grounded": 0, "ungrounded": 0},
        "environmental material": {"grounded": 0, "ungrounded": 0},
        "contains measurements of type": {"grounded": 0, "ungrounded": 0},
        "uses standard": {"grounded": 0, "ungrounded": 0},
        "usesMethod": {"grounded": 0, "ungrounded": 0},
        "research topic": {"grounded": 0, "ungrounded": 0},
    }

    files = [f for f in os.listdir(test_dir) if f.endswith(".tsv")]
    for file in files:
        path = os.path.join(test_dir, file)
        logger.info(f"Getting grounding rates for {path}")
        wb = load_workbook(path)
        wb = delete_unannotated_rows(wb)  # OntoGPT skipped these, don't count

        # Group object_ids by predicate and element_xpath. These represent
        # unique annotation opportunities for OntoGPT to ground to an ontology.
        object_id_groups = group_object_ids(wb)

        # For each group determine if the object_ids are grounded or ungrounded
        for key, data in object_id_groups.items():
            predicate = key[0]
            if is_grounded(data):
                res[predicate]["grounded"] += 1
            else:
                res[predicate]["ungrounded"] += 1
    return res


def is_grounded(data: list) -> bool:
    """
    Determine if the list contains a grounded object_id.

    :param data: List of object_ids.
    :return: True if the list contains a grounded object_id, False otherwise.
        A grounded term is defined as a term that starts with "http".
        Ungrounded terms are those that begin with "AUTO:" or are None.
    """
    # Remove None and NaN values from list to avoid errors on string matching
    data = [d for d in data if d is not None]
    data = [d for d in data if not pd.isna(d)]

    return any("http" in s for s in data)


def plot_similarity_scores_by_predicate(
    benchmark_results: pd.DataFrame,
    test_dir_path: str,
    metric: str,
    output_file: str = None,
) -> None:
    """
    To see predicate level performance for an OntoGPT test configuration

    :param benchmark_results: The return value from the
        `benchmark_against_standard` function.
    :param test_dir_path: Path to the test directory containing the test
        annotated workbook files for the desired configuration. This should be
        a value from the `test_dir` column of the benchmark_results DataFrame,
        which indicates the configuration comparison to plot.
    :param metric: The metric to plot. This should be a column name from the
        benchmark_results DataFrame, e.g. "average_score", "best_score", etc.
    :param output_file: The path to save the plot to, as a PNG file.
    :return: None
    """
    # Subset the benchmark results dataframe to only include the desired
    # columns: test_dir, metric
    df = benchmark_results[benchmark_results["test_dir"] == test_dir_path][
        ["predicate_value", metric]
    ]

    # Remove empty rows where the metric is 0 or NaN to avoid plotting them
    df = df.dropna(subset=[metric])
    df = df[df[metric] != 0]

    # Order the "predicate_value" column to ensure the plot's x-axis is ordered
    # correctly
    df["predicate_value"] = pd.Categorical(
        df["predicate_value"],
        [
            "env_broad_scale",
            "env_local_scale",
            "contains process",
            "environmental material",
            "contains measurements of type",
            "uses standard",
            "usesMethod",
            "research topic",
        ],
    )

    plt.figure(figsize=(10, 6))
    grouped_data_long = df.groupby("predicate_value")[metric].apply(list)
    plt.boxplot(
        grouped_data_long.values, labels=grouped_data_long.index, showmeans=True
    )

    # Add individual data points (jittered)
    for i, group_data in enumerate(grouped_data_long):
        x = np.random.normal(i + 1, 0.08, size=len(group_data))  # Jitter x-values
        plt.plot(x, group_data, "o", alpha=0.25, color="grey")

    configuration = os.path.basename(test_dir_path)

    plt.xlabel("Predicate")
    plt.ylabel("Score")
    title = (
        f"Similarity Score '{metric}' Against Benchmark Standard for "
        f"Configuration '{configuration}'"
    )
    plt.title(title)
    plt.xticks(rotation=-20)
    plt.tight_layout()
    if output_file:
        plt.savefig(output_file, dpi=300)
    plt.show()


def plot_similarity_scores_by_configuration(
    benchmark_results: pd.DataFrame,
    metric: str,
    output_file: str = None,
) -> None:
    """
    To see configuration level performance for an OntoGPT predicate

    :param benchmark_results: The return value from the
        `benchmark_against_standard` function.
    :param metric: The metric to plot. This should be a column name from the
        benchmark_results DataFrame, e.g. "average_score", "best_score", etc.
    :param output_file: The path to save the plot to, as a PNG file.
    :return: None
    """
    # Subset the benchmark results dataframe to only include the desired
    # columns: test_dir, metric
    df = benchmark_results[["test_dir", metric]]

    # Remove empty rows where the metric is 0 or NaN to avoid plotting them
    df = df.dropna(subset=[metric])
    df = df[df[metric] != 0]

    plt.figure(figsize=(10, 6))
    grouped_data_long = df.groupby("test_dir")[metric].apply(list)
    plt.boxplot(
        grouped_data_long.values, labels=grouped_data_long.index, showmeans=True
    )

    # Add individual data points (jittered)
    for i, group_data in enumerate(grouped_data_long):
        x = np.random.normal(i + 1, 0.08, size=len(group_data))  # Jitter x-values
        plt.plot(x, group_data, "o", alpha=0.25, color="grey")

    plt.xlabel("Configuration")
    plt.ylabel("Score")
    title = f"Similarity Score '{metric}' Across Configurations"
    plt.title(title)
    plt.xticks(rotation=-20)
    plt.tight_layout()
    if output_file:
        plt.savefig(output_file, dpi=300)
    plt.show()
