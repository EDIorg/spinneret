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
    calculate_unresolvable_geometry_percentage,
    summarize_geoenv_directory,
    reformat_environments_to_long,
    prepare_plotting_data,
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

    assert len(empty_files) == 2


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

    assert result == 5


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
    assert total_unique == 8


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


def test_calculate_unresolvable_geometry_percentage():
    """Test that the calculate_unresolvable_geometry_percentage function can
    calculate the percentage of geometries that have no environments."""
    directory = files("tests.data.geoenv")
    percent = calculate_unresolvable_geometry_percentage(directory)

    # Based on fixture assumptions: 2 of 8 geometries has no environments
    assert percent == 25.0


def test_summarize_geoenv_directory():
    """Test that the summarize_geoenv_directory function can summarize key
    metrics from geoenv JSON files in a directory."""
    directory = files("tests.data.geoenv")
    summary = summarize_geoenv_directory(directory)

    # Ensure summary is a dictionary
    assert isinstance(summary, dict)

    # Required keys should be present
    expected_keys = {
        "unique_datasets",
        "unique_geometries",
        "unique_environments",
        "unique_environments_by_data_source",
        "unresolvable_geometry_percentage",
    }
    assert expected_keys.issubset(summary.keys())

    # Check data types
    assert isinstance(summary["unique_datasets"], int)
    assert isinstance(summary["unique_geometries"], int)
    assert isinstance(summary["unique_environments"], int)
    assert isinstance(summary["unique_environments_by_data_source"], dict)
    assert isinstance(summary["unresolvable_geometry_percentage"], float)

    # Spot-check known values from fixture set
    assert summary["unique_datasets"] == 5
    assert summary["unique_geometries"] == 8
    assert summary["unique_environments"] == 9
    assert summary["unresolvable_geometry_percentage"] == 25.0

    # Check expected sources in environment breakdown
    expected_sources = {
        "WorldTerrestrialEcosystems",
        "EcologicalMarineUnits",
        "EcologicalCoastalUnits",
    }
    assert expected_sources.issubset(
        summary["unique_environments_by_data_source"].keys()
    )


def test_reformat_environments_to_long():
    """Test that the reformat_environments_to_long function can reformat a
    wide DataFrame into a long format."""
    df_wide = load_all_environments(files("tests.data.geoenv"))
    df_long = reformat_environments_to_long(df_wide)

    # Check type and structure
    assert isinstance(df_long, pd.DataFrame)
    assert set(df_long.columns) == {"identifier", "dataSource", "property", "value"}

    # There should be more rows in long format than in wide format
    assert len(df_long) > len(df_wide)

    # Spot-check some known values
    assert "temperature" in df_long["property"].values
    assert "salinity" in df_long["property"].values

    # Check that no null values remain in the 'value' column
    assert df_long["value"].isnull().sum() == 0

    # Check that all rows have an identifier and dataSource
    assert df_long["identifier"].isnull().sum() == 0
    assert df_long["dataSource"].isnull().sum() == 0


def test_prepare_plotting_data():
    """Test that the prepare_plotting_data function removes duplicates,
    drops the 'ecosystem' property, and groups by 'dataSource', 'property',
    and 'value'."""
    # Sample data
    data = {
        "identifier": ["id1", "id2", "id3", "id1"],
        "dataSource": ["source1", "source1", "source2", "source1"],
        "property1": [10, 20, 30, 10],
        "ecosystem": ["eco1", "eco2", "eco3", "eco1"],
    }
    df_long = reformat_environments_to_long(pd.DataFrame(data))

    # Call the function
    df_grouped = prepare_plotting_data(df_long)

    # Check that there are no duplicates
    assert df_grouped.duplicated().sum() == 0

    # Check that the 'ecosystem' property has been removed
    assert "ecosystem" not in df_grouped.columns

    # Check that the returned DataFrame is grouped by 'dataSource', 'property',
    # and 'value'
    expected_columns = {"dataSource", "property", "value", "count"}
    assert set(df_grouped.columns) == expected_columns

    # Check that the counts are correct
    expected_counts = {
        ("source1", "property1", 10): 1,
        ("source1", "property1", 20): 1,
        ("source2", "property1", 30): 1,
    }
    for _, row in df_grouped.iterrows():
        key = (row["dataSource"], row["property"], row["value"])
        assert row["count"] == expected_counts[key]
