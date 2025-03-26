"""For testing the plot module."""

from importlib.resources import files
import pandas as pd
from spinneret.plot import extract_environments_from_file, load_all_environments


def test_extract_environments_from_file():
    """Test that the extract_environments_from_file function can extract
    environment records from a geoenv JSON file."""
    base_path = files("tests.data.geoenv")
    filenames = [f for f in base_path.iterdir() if f.suffix == ".json"]

    # all_records = []
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
