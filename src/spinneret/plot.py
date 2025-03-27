"""The plot module provides a simple interface for plotting data."""

import hashlib
import json
from pathlib import PosixPath
from typing import List, Set

import pandas as pd
from importlib_resources.readers import MultiplexedPath


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
