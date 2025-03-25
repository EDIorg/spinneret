"""The plot module provides a simple interface for plotting data."""

import json
from pathlib import PosixPath
from typing import List

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
        dataset_id = feature.get("identifier")
        for env in feature.get("properties", {}).get("environment", []):
            data_source = env.get("dataSource", {})
            base_record = {
                "dataset_id": dataset_id,
                "data_source_name": data_source.get("name"),
                "data_source_identifier": data_source.get("identifier"),
                "date_created": env.get("dateCreated"),
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
