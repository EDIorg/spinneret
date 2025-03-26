"""For testing the plot module."""

import shutil
from importlib.resources import files
import pandas as pd
from spinneret.plot import (
    extract_environments_from_file,
    load_all_environments,
    find_empty_extractions,
    count_unique_environments,
    count_unique_datasets,
    count_unique_geometries,
    count_unique_environments_by_data_source,
)


def test_extract_environments_from_file():
    """Test that the extract_environments_from_file function can extract
    environment records from a geoenv JSON file."""
    base_path = files("tests.data.geoenv")
    filenames = [f for f in base_path.iterdir() if f.suffix == ".json"]

    for fname in filenames:
        records = extract_environments_from_file(fname)

        # Case of empty record
        if "knb-lter-and.3147.7.json" in str(fname):
            assert len(records) == 0
            continue

        # Basic shape expectations
        assert isinstance(records, list)
        basic_vars = {"identifier", "dataSource"}
        for rec in records:
            for var in basic_vars:
                assert var in rec
            assert len(rec) > 2  # Assert other properties are present


def test_load_all_environments_combines_records():
    """Test that the load_all_environments function can combine records from
    multiple geoenv JSON results."""
    base_path = files("tests.data.geoenv")
    all_records = load_all_environments(base_path)

    # Convert to DataFrame for easier assertions
    df = pd.DataFrame(all_records)

    # Basic shape expectations
    basic_vars = {"identifier", "dataSource"}
    for var in basic_vars:
        assert var in df.columns
    assert len(df) == 12

    # Check that specific known sources are present
    expected_sources = {
        "WorldTerrestrialEcosystems",
        "EcologicalCoastalUnits",
        "EcologicalMarineUnits",
    }
    assert expected_sources.issubset(set(df["dataSource"].dropna()))

    # Check some known properties are included somewhere in the data
    properties = set(df.columns) - basic_vars
    expected_properties = {
        "chlorophyll",
        "landForm",
        "landCover",
        "ecosystem",
        "climate",
        "tidalRange",
        "marinePhysicalEnvironment",
        "sinuosity",
        "slope",
        "waveHeight",
        "moisture",
        "riverDischarge",
        "depth",
        "nitrate",
        "salinity",
        "temperatureAndMoistureRegime",
        "erodibility",
        "dissolvedOxygen",
        "silicate",
        "temperature",
        "turbidity",
        "oceanName",
        "phosphate",
    }
    assert expected_properties.issubset(properties)


def test_load_all_environments_with_empty_folder(tmp_path):
    """Test that the load_all_environments function can handle an empty
    folder."""
    df = load_all_environments(tmp_path)
    assert len(df) == 0


def test_find_empty_extractions():
    """Test that the find_empty_extractions function can identify files that
    produced no extracted environment records."""
    empty_files = find_empty_extractions(files("tests.data.geoenv"))

    assert len(empty_files) == 1
    assert empty_files[0].endswith("knb-lter-and.3147.7.json")


def test_find_empty_extractions_with_empty_folder(tmp_path):
    """Test that the find_empty_extractions function can handle an empty
    folder."""
    empty_files = find_empty_extractions(tmp_path)
    assert isinstance(empty_files, list)
    assert len(empty_files) == 0


def test_count_unique_environments():
    """Test that the count_unique_environments function can count unique
    environments from JSON files."""
    unique_environments = count_unique_environments(files("tests.data.geoenv"))
    assert unique_environments == 9


def test_count_unique_environments_with_empty_folder(tmp_path):
    """Test that the count_unique_environments function can handle an empty
    folder."""
    unique_environments = count_unique_environments(tmp_path)
    assert unique_environments == 0


def test_count_unique_datasets_from_fixture_dir():
    """Test that the count_unique_datasets function can count unique datasets
    from JSON files."""
    directory = files("tests.data.geoenv")
    result = count_unique_datasets(directory)

    assert result == 4


def test_count_unique_datasets_from_empty_dir(tmp_path):
    """Test that the count_unique_datasets function can handle an empty
    folder."""
    result = count_unique_datasets(tmp_path)

    assert result == 0


def test_count_unique_geometries():
    """Test that the count_unique_geometries function can count the total
    number of unique geometries across all JSON files in a directory."""
    total_unique = count_unique_geometries(files("tests.data.geoenv"))

    # Expecting 3 total unique geometries in current fixture set
    assert total_unique == 7


def test_count_unique_geometries_with_empty_geometry_file(tmp_path):
    """Test that the count_unique_geometries function can handle a file with
    no geometries."""
    # Move empty geometry file to tmp_path for testing
    empty_file = files("tests.data.geoenv").joinpath("knb-lter-and.3147.7.json")
    shutil.copy(empty_file, tmp_path / empty_file.name)
    assert count_unique_geometries(tmp_path) == 0


def test_count_unique_environments_by_data_source():
    """Test that the count_unique_environments_by_data_source function can
    count unique environments by data source."""
    directory = files("tests.data.geoenv")
    result = count_unique_environments_by_data_source(directory)

    # Expected keys from the test fixture data
    expected = {
        "EcologicalCoastalUnits": 5,
        "EcologicalMarineUnits": 1,
        "WorldTerrestrialEcosystems": 3,
    }

    # Check that the result is a dictionary with the expected keys
    assert isinstance(result, dict)
    assert set(result.keys()) == set(expected.keys())

    # pylint: disable=unnecessary-dict-index-lookup
    # Check that the counts match the expected values
    for key, _ in expected.items():
        assert result[key] == expected[key]
