"""For testing the plot module."""

from importlib.resources import files
import pandas as pd
from spinneret.plot import extract_environments_from_file, load_all_environments


def test_different_data_source_parsing():
    """Test that the extract_environments_from_file function can parse the
    geoenv JSON result with a different data source."""
    path = files("tests.data.geoenv").joinpath("different_data_source.json")
    results = extract_environments_from_file(path)

    assert len(results) == 1
    record = results[0]
    assert record["data_source_name"] == "LandSurfaceData"
    assert record["landCover"] == "Grassland"
    assert record["surfaceTemperature"] == "Warm"


def test_extract_basic_environment():
    """Test that the extract_environments_from_file function can parse the
    geoenv JSON result with a basic environment."""
    path = files("tests.data.geoenv").joinpath("basic_example.json")
    results = extract_environments_from_file(path)

    assert len(results) == 1
    record = results[0]
    assert record["dataset_id"] == "test-id-001"
    assert record["data_source_name"] == "TestDataSource"
    assert record["data_source_identifier"] == "doi:1234"
    assert record["date_created"] == "2025-03-25 00:00:00"
    assert record["temperature"] == "Cold"
    assert record["salinity"] == "Euhaline"


def test_extract_different_data_source():
    """Test that the extract_environments_from_file function can parse the
    geoenv JSON result with a different data source."""
    path = files("tests.data.geoenv").joinpath("different_data_source.json")
    results = extract_environments_from_file(path)

    assert len(results) == 1
    record = results[0]
    assert record["dataset_id"] == "test-id-002"
    assert record["data_source_name"] == "LandSurfaceData"
    assert record["data_source_identifier"] == "doi:5678"
    assert record["landCover"] == "Grassland"
    assert record["soilMoisture"] == "Moderate"
    assert record["surfaceTemperature"] == "Warm"


def test_extract_multiple_environments():
    """Test that the extract_environments_from_file function can parse the""
    geoenv JSON result with multiple environments."""
    path = files("tests.data.geoenv").joinpath("multiple_environments.json")
    results = extract_environments_from_file(path)

    assert len(results) == 2

    # Sort by data_source_name to keep test order deterministic
    results.sort(key=lambda r: r["data_source_name"])

    # pylint: disable=unbalanced-tuple-unpacking
    first, second = results

    assert first["data_source_name"] == "DeepSeaProfiles"
    assert first["depthZone"] == "Abyssopelagic"
    assert first["pressure"] == "High"

    assert second["data_source_name"] == "EcoOcean"
    assert second["oxygenLevel"] == "High"
    assert second["chlorophyll"] == "Low"


def test_extract_with_no_environments():
    """Test that the extract_environments_from_file function can handle a
    geoenv JSON result with no environments."""
    path = files("tests.data.geoenv").joinpath("incomplete_environment.json")
    results = extract_environments_from_file(path)

    # Should return an empty list
    assert not results


def test_load_all_environments_combines_records():
    """Test that the load_all_environments function can combine records from
    multiple geoenv JSON results."""
    directory = files("tests.data.geoenv")
    df = load_all_environments(directory)

    # Check it returns a DataFrame
    assert isinstance(df, pd.DataFrame)

    # Expecting:
    # - 1 env in basic_example
    # - 1 env in different_data_source
    # - 2 envs in multiple_environments
    # - 0 in incomplete_environment
    assert len(df) == 4

    # Make sure some expected columns are present
    expected_columns = {
        "dataset_id",
        "data_source_name",
        "data_source_identifier",
        "date_created",
    }
    assert expected_columns.issubset(df.columns)

    # Spot-check some values
    assert "TestDataSource" in df["data_source_name"].values
    assert "LandSurfaceData" in df["data_source_name"].values
    assert "EcoOcean" in df["data_source_name"].values
