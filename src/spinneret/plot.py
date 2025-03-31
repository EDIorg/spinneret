"""The plot module provides a simple interface for plotting data."""

import hashlib
import json
from pathlib import PosixPath
from typing import List, Set
import matplotlib.pyplot as plt

import pandas as pd
from importlib_resources.readers import MultiplexedPath
from matplotlib.patheffects import withStroke


def extract_environments_from_file(file_path: PosixPath) -> List[dict]:
    """
    Extracts the environment data from a geoenv JSON file.
    :param file_path: Path to the geoenv JSON file.
    :return: The extracted environment data.
    """
    with open(file_path, encoding="utf-8") as f:
        content = json.load(f)

    records = []

    for feature in content.get("data", []):
        identifier = feature.get("identifier")
        for env in feature.get("properties", {}).get("environment", []):
            data_source = env.get("dataSource", {})
            base_record = {
                "identifier": identifier,
                "dataSource": data_source.get("name"),
            }
            env_props = env.get("properties", {})
            full_record = {**base_record, **env_props}
            records.append(full_record)

    return records


def load_all_environments(json_folder_path: MultiplexedPath) -> pd.DataFrame:
    """
    Load all the environments from a folder of geoenv JSON files.
    :param json_folder_path: Path to the folder containing the geoenv JSON files.
    :return: A DataFrame containing all the environments.
    """
    all_records = []
    for path in json_folder_path.iterdir():
        if path.suffix != ".json":
            continue
        all_records.extend(extract_environments_from_file(path))
    return pd.DataFrame(all_records)


def find_empty_extractions(json_folder_path: MultiplexedPath) -> List[str]:
    """
    Returns a list of file paths in the given json_folder_path that produced
    no extracted environment records.

    :param json_folder_path: Path to the folder containing the geoenv JSON
        files.
    :return: List of file paths that produced no extracted environment records.
    """
    empty_files = []
    for file_path in json_folder_path.iterdir():
        if file_path.suffix != ".json":
            continue
        records = extract_environments_from_file(file_path)
        if not records:  # Empty list means no environments found
            empty_files.append(str(file_path))

    return empty_files


def count_unique_environments(directory: MultiplexedPath) -> int:
    """
    Counts all unique environments from JSON files in the given directory
    :param directory: Path to the folder containing the geoenv JSON files.
    :return: The number of unique environments
    """
    df = load_all_environments(directory)
    if df.empty:
        return 0

    # Drop columns that are not environment properties
    df = df.drop(columns=["identifier", "dataSource"])

    return len(df.drop_duplicates())


def count_unique_environments_by_data_source(directory: MultiplexedPath) -> dict:
    """
    Counts all unique environments from JSON files in the given directory by
    dataSource.

    :param directory: Path to the folder containing the geoenv JSON files.
    :return: A dictionary with keys for each dataSource and values being the
        total count for each dataSource.
    """
    df = load_all_environments(directory)
    if df.empty:
        return {}

    # Drop columns that could affect the uniqueness of the rows
    df = df.drop(columns=["identifier"])

    # Drop duplicate rows, and count up dataSource occurrences
    unique_counts = df.drop_duplicates().groupby("dataSource").size().to_dict()

    return unique_counts


def count_unique_datasets(directory: MultiplexedPath) -> int:
    """
    Counts the number of unique datasets in a directory. Assumes each .json
    file represents one dataset.
    :param directory: Path to the folder containing the geoenv JSON files.
    """
    return len([f for f in directory.iterdir() if f.suffix == ".json"])


def count_unique_geometries(directory: MultiplexedPath) -> int:
    """
    Counts the total number of unique geometries across all JSON files in a directory.
    Deduplicates geometries by content (based on GeoJSON structure).
    """
    global_geometries: Set[str] = set()

    for file_path in directory.iterdir():
        if file_path.suffix != ".json":
            continue
        with open(file_path, encoding="utf-8") as f:
            content = json.load(f)

        for feature in content.get("data", []):
            geom = feature.get("geometry")
            if geom:
                geom_str = json.dumps(geom, sort_keys=True)
                geom_hash = hashlib.md5(geom_str.encode()).hexdigest()
                global_geometries.add(geom_hash)

    return len(global_geometries)


def calculate_unresolvable_geometry_percentage(directory: MultiplexedPath) -> float:
    """
    Calculates the percentage of geometries that could not be resolved (i.e.,
    have an empty or missing environment list). Only counts features that
    contain a geometry.

    :param directory: Path to directory containing geoenv JSON files.
    :return: Percentage (0–100) of geometries that are non-resolvable.
    """
    total_with_geometry = 0
    unresolved_with_geometry = 0

    for file_path in directory.iterdir():
        if file_path.suffix != ".json":
            continue
        with open(file_path, encoding="utf-8") as f:
            content = json.load(f)

        for feature in content.get("data", []):
            geometry = feature.get("geometry")
            if geometry:
                total_with_geometry += 1

                env = feature.get("properties", {}).get("environment", [])
                if not env:
                    unresolved_with_geometry += 1

    if total_with_geometry == 0:
        return (
            0.0  # Avoid divide-by-zero; define as 0% unresolved if no geometries exist
        )

    percentage = (unresolved_with_geometry / total_with_geometry) * 100
    return round(percentage, 2)


def summarize_geoenv_directory(directory: MultiplexedPath) -> dict:
    """
    Summarizes key metrics from geoenv JSON files in a directory.

    :param directory: Path to the directory of geoenv JSON files.
    :return: A dictionary of metric names and their values.
    """

    summary = {
        "unique_datasets": count_unique_datasets(directory),
        "unique_geometries": count_unique_geometries(directory),
        "unique_environments": count_unique_environments(directory),
        "unique_environments_by_data_source": count_unique_environments_by_data_source(
            directory
        ),
        "unresolvable_geometry_percentage": calculate_unresolvable_geometry_percentage(
            directory
        ),
    }

    # Print summary
    print("\n📊 GeoEnv Summary")
    print("-" * 30)
    print(f"📁 Unique datasets: {summary['unique_datasets']}")
    print(f"🌐 Unique geometries: {summary['unique_geometries']}")
    print(f"🌎 Unique environments: {summary['unique_environments']}")
    print("📀 Unique environments by data source:")
    for source, props in summary["unique_environments_by_data_source"].items():
        print(f"    - {source}: {props}")
    print(f"❌ Unresolvable geometry %: {summary['unresolvable_geometry_percentage']}")
    print("-" * 30)

    return summary


def reformat_environments_to_long(df: pd.DataFrame) -> pd.DataFrame:
    """
    Reformats the environment DataFrame from wide format to long format.
    Treats 'identifier' and 'dataSource' as ID variables.

    :param df: DataFrame in wide format from load_all_environments().
    :return: Long-format DataFrame with columns ['identifier', 'dataSource', 'property', 'value'].
    """
    id_vars = ["identifier", "dataSource"]

    # Determine value columns (environment properties)
    value_vars = [col for col in df.columns if col not in id_vars]

    df_long = pd.melt(
        df,
        id_vars=id_vars,
        value_vars=value_vars,
        var_name="property",
        value_name="value",
    )

    # Optionally drop rows where value is missing
    df_long = df_long.dropna(subset=["value"])

    # Sort the DataFrame for better readability
    df_long = df_long.sort_values(by=["identifier", "dataSource", "property"])

    return df_long


def prepare_plotting_data(df_long: pd.DataFrame) -> pd.DataFrame:
    """
    Prepares data for plotting by:
    - Removing duplicate rows
    - Grouping by dataSource, property, value
    - Counting unique identifiers
    """
    df_clean = df_long.drop_duplicates()

    # Remove the `ecosystem` property due to its low information density and
    # performance impact. This property, a concatenation of all environmental
    # properties, generates numerous unhelpful permutations and significantly
    # increases processing time during plot generation.
    df_clean = df_clean[df_clean["property"] != "ecosystem"]

    grouped = (
        df_clean.groupby(["dataSource", "property", "value"])["identifier"]
        .nunique()
        .reset_index()
        .rename(columns={"identifier": "count"})
    )
    return grouped

# pylint: disable=too-many-locals
def plot_grouped_bar_charts(df_grouped: pd.DataFrame, output_dir: str) -> None:
    """
    Generates horizontal bar plots grouped by dataSource and property.
    Each value is labeled inside the bar if space permits; otherwise, it's placed outside.

    :param df_grouped: DataFrame with columns ['dataSource', 'property', 'value', 'count']
    :param output_dir: Directory where .png files will be saved.
    """
    for data_source in df_grouped["dataSource"].unique():
        df_subset = df_grouped[df_grouped["dataSource"] == data_source]
        for data_source_property in df_subset["property"].unique():
            df_subset2 = df_subset[
                df_subset["property"] == data_source_property
            ].sort_values(by=["count"], ascending=True)

            counts = df_subset2["count"].values.tolist()
            names = df_subset2["value"].values.tolist()
            y = [i * 0.9 for i in range(len(names))]

            fig, ax = plt.subplots(figsize=(12, 7))
            ax.barh(y, counts, height=0.55, align="edge", color="#076fa2")

            x_tick_interval = 20 if max(counts) >= 200 else 10
            ax.xaxis.set_ticks(list(range(0, max(counts), x_tick_interval)))
            ax.xaxis.set_ticklabels(
                list(range(0, max(counts), x_tick_interval)), size=16, fontweight=100
            )
            ax.xaxis.set_tick_params(labelbottom=False, labeltop=True, length=0)
            ax.set_xlim((0, max(counts) + 10))
            ax.set_ylim((0, len(names) * 0.9 - 0.2))
            ax.set_axisbelow(True)
            ax.grid(axis="x", color="#A8BAC4", lw=1.2)
            ax.spines["right"].set_visible(False)
            ax.spines["top"].set_visible(False)
            ax.spines["bottom"].set_visible(False)
            ax.spines["left"].set_lw(1.5)
            ax.spines["left"].set_capstyle("butt")
            ax.yaxis.set_visible(False)

            pad = 0.3
            for name, count, y_pos in zip(names, counts, y):
                ax.text(
                    0 + pad,
                    y_pos + 0.5 / 2,
                    name,
                    color="none",
                    fontsize=18,
                    va="center",
                )
                x_text_end = ax.texts[-1].get_window_extent().x1
                ax.plot(count, y_pos, ".", color="none", markersize=18)
                x_point = ax.lines[-1].get_window_extent().x1
                position_label_to_right_of_bar = x_text_end > x_point

                color = "#076fa2" if position_label_to_right_of_bar else "lightgrey"
                path_effects = (
                    [withStroke(linewidth=6, foreground="white")]
                    if position_label_to_right_of_bar
                    else None
                )
                ax.text(
                    count + pad if position_label_to_right_of_bar else 0 + pad,
                    y_pos + 0.5 / 2,
                    name,
                    color=color,
                    fontsize=18,
                    va="center",
                    path_effects=path_effects,
                )

            fig.subplots_adjust(left=0.05, right=1, top=0.8, bottom=0.1)
            ax.set_xlabel("Number of Datasets", size=18, fontweight=100)
            ax.xaxis.set_label_coords(0.5, 1.14)
            fig.text(
                0.05,
                0.925,
                f"{data_source} - {data_source_property}",
                fontsize=22,
                fontweight="bold",
            )
            fig.set_facecolor("white")
            fig.savefig(
                f"{output_dir}{data_source} - {data_source_property}.png", dpi=300
            )


if __name__ == "__main__":

    results_directory = MultiplexedPath(
        "/Users/csmith/Data/testing_geoenvo/full_batch/responses"
    )

    # # Generate summary of geoenv directory
    # summary = summarize_geoenv_directory(results_directory)

    # Load and reformat data
    all_env_df = load_all_environments(results_directory)
    long_df = reformat_environments_to_long(all_env_df)
    grouped_df = prepare_plotting_data(long_df)

    # Create and save plots
    plot_grouped_bar_charts(
        grouped_df, output_dir="/Users/csmith/Data/testing_geoenvo/full_batch/plots/"
    )
