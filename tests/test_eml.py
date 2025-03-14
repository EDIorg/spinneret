"""Tests for the eml module."""

from json import dumps
from importlib.resources import files
from unittest.mock import patch
import pytest
from spinneret import eml
from spinneret.eml import get_geographic_coverage


@pytest.fixture(name="geocov")
def geocov_fixture():
    """A list of GeographicCoverage instances from the test EML file."""
    eml_file = str(files("spinneret.data.eml").joinpath("edi.1.1.xml"))
    with open(eml_file, "r", encoding="utf-8") as f:
        res = get_geographic_coverage(eml=f)
    return res


def test_get_geographic_coverage(geocov):
    """Test get_geographic_coverage function."""
    assert isinstance(geocov, list)
    for item in geocov:
        assert isinstance(item, eml.GeographicCoverage)


def test_geom_type(geocov):
    """Test geographicCoverage geom_type method

    This is a fixture based on the contents of edi.1.1.xml. This fixture
    should be updated whenever that files geographicCoverage changes.
    """
    assert geocov[0].geom_type() == "envelope"
    assert geocov[1].geom_type() == "point"
    assert geocov[2].geom_type() == "polygon"
    assert geocov[0].geom_type(schema="esri") == "esriGeometryEnvelope"
    assert geocov[1].geom_type(schema="esri") == "esriGeometryPoint"
    assert geocov[2].geom_type(schema="esri") == "esriGeometryPolygon"


def test_to_esri_geometry(geocov):
    """Test geographicCoverage to_esri_geometry method

    Envelopes are converted to esriGeometryEnvelope, points to
    esriGeometryEnvelope, and polygons to esriGeometryPolygon.
    """
    # Envelope to envelope
    g = geocov[0]  # An envelope without units
    assert g.to_esri_geometry() == dumps(
        {
            "xmin": -123.552,
            "ymin": 39.804,
            "xmax": -120.83,
            "ymax": 40.441,
            "zmin": None,
            "zmax": None,
            "spatialReference": {"wkid": 4326},
        }
    )

    # Point to envelope
    g = geocov[1]  # A point without units
    assert g.to_esri_geometry() == dumps(
        {
            "xmin": -72.22,
            "ymin": 42.48,
            "xmax": -72.22,
            "ymax": 42.48,
            "zmin": None,
            "zmax": None,
            "spatialReference": {"wkid": 4326},
        }
    )

    # Point to envelope
    g = geocov[11]  # A point with units
    assert g.to_esri_geometry() == dumps(
        {
            "xmin": -157.875,
            "ymin": 21.125,
            "xmax": -157.875,
            "ymax": 21.125,
            "zmin": -15.0,
            "zmax": 0.0,
            "spatialReference": {"wkid": 4326},
        }
    )

    # Polygon to polygon
    g = geocov[2]
    assert g.to_esri_geometry() == dumps(
        {
            "rings": [
                [
                    [-123.7976226, 39.3085666],
                    [-123.8222818, 39.3141049],
                    [-123.8166231, 39.2943269],
                    [-123.7976226, 39.3085666],
                ],
                [
                    [-123.8078563, 39.3068951],
                    [-123.8163387, 39.3086898],
                    [-123.813222, 39.3022756],
                    [-123.8078177, 39.3068354],
                    [-123.8078563, 39.3068951],
                ],
            ],
            "spatialReference": {"wkid": 4326},
        }
    )


def test_description(geocov):
    """Test geographicCoverage description method

    This is a fixture based on the contents of edi.1.1.xml. This fixture
    should be updated whenever that files geographicCoverage changes.
    """
    assert isinstance(geocov[0].description(), str)
    geocov[0].gc.remove(geocov[0].gc.find(".//geographicDescription"))
    assert geocov[0].description() is None


def test_west(geocov):
    """Test geographicCoverage west method

    This is a fixture based on the contents of edi.1.1.xml. This fixture
    should be updated whenever that files geographicCoverage changes.
    """
    assert isinstance(geocov[0].west(), float)
    geocov[0].gc.remove(geocov[0].gc.find(".//westBoundingCoordinate").getparent())
    assert geocov[0].west() is None


def test_east(geocov):
    """Test geographicCoverage east method

    This is a fixture based on the contents of edi.1.1.xml. This fixture
    should be updated whenever that files geographicCoverage changes.
    """
    assert isinstance(geocov[0].east(), float)
    geocov[0].gc.remove(geocov[0].gc.find(".//eastBoundingCoordinate").getparent())
    assert geocov[0].east() is None


def test_north(geocov):
    """Test geographicCoverage north_bounding_coordinate method

    This is a fixture based on the contents of edi.1.1.xml. This fixture
    should be updated whenever that files geographicCoverage changes.
    """
    assert isinstance(geocov[0].north(), float)
    geocov[0].gc.remove(geocov[0].gc.find(".//northBoundingCoordinate").getparent())
    assert geocov[0].north() is None


def test_south(geocov):
    """Test geographicCoverage south_bounding_coordinate method

    This is a fixture based on the contents of edi.1.1.xml. This fixture
    should be updated whenever that files geographicCoverage changes.
    """
    assert isinstance(geocov[0].south(), float)
    geocov[0].gc.remove(geocov[0].gc.find(".//southBoundingCoordinate").getparent())
    assert geocov[0].south() is None


def test_outer_gring(geocov):
    """Test geographicCoverage outer_gring method

    This is a fixture based on the contents of edi.1.1.xml. This fixture
    should be updated whenever that files geographicCoverage changes.
    """
    assert isinstance(geocov[2].outer_gring(), str)
    geocov[2].gc.remove(geocov[2].gc.find(".//datasetGPolygonOuterGRing").getparent())
    assert geocov[2].outer_gring() is None


def test_exclusion_gring(geocov):
    """Test geographicCoverage exclusion_gring method

    This is a fixture based on the contents of edi.1.1.xml. This fixture
    should be updated whenever that files geographicCoverage changes.
    """
    assert isinstance(geocov[2].exclusion_gring(), str)
    geocov[2].gc.remove(
        geocov[2].gc.find(".//datasetGPolygonExclusionGRing").getparent()
    )
    assert geocov[2].exclusion_gring() is None


def test_altitude_minimum(geocov):
    """Test geographicCoverage altitude_minimum method"""
    g = geocov[11]  # A geographic coverage with altitudes in meters
    assert isinstance(g.altitude_minimum(), float)
    assert g.altitude_minimum() == -15
    # The _convert_to_meters method should be called when the to_meters
    # argument is True.
    with patch(
        "spinneret.eml.GeographicCoverage._convert_to_meters"
    ) as mock__convert_to_meters:
        g.altitude_minimum(to_meters=True)
        mock__convert_to_meters.assert_called_once()
    # The _convert_to_meters method should not be called when the to_meters
    # argument is False.
    with patch(
        "spinneret.eml.GeographicCoverage._convert_to_meters"
    ) as mock__convert_to_meters:
        g.altitude_minimum(to_meters=False)
        mock__convert_to_meters.assert_not_called()
    # Returns None when no altitudeMinimum element is present.
    g.gc.remove(g.gc.find(".//altitudeMinimum").getparent())
    assert g.altitude_minimum() is None


def test_altitude_maximum(geocov):
    """Test geographicCoverage altitude_maximum method"""
    g = geocov[11]  # A geographic coverage with altitudes in meters
    assert isinstance(g.altitude_maximum(), float)
    assert g.altitude_maximum() == 0
    # The _convert_to_meters method should be called when the to_meters
    # argument is True.
    with patch(
        "spinneret.eml.GeographicCoverage._convert_to_meters"
    ) as mock__convert_to_meters:
        g.altitude_maximum(to_meters=True)
        mock__convert_to_meters.assert_called_once()
    # The _convert_to_meters method should not be called when the to_meters
    # argument is False.
    with patch(
        "spinneret.eml.GeographicCoverage._convert_to_meters"
    ) as mock__convert_to_meters:
        g.altitude_maximum(to_meters=False)
        mock__convert_to_meters.assert_not_called()
    # Returns None when no altitudeMinimum element is present.
    g.gc.remove(g.gc.find(".//altitudeMaximum").getparent())
    assert g.altitude_maximum() is None


def test_altitude_units(geocov):
    """Test geographicCoverage altitude_units method"""
    g = geocov[11]  # A geographic coverage with altitude in units of feet
    assert isinstance(g.altitude_units(), str)
    assert g.altitude_units() == "meter"
    g.gc.remove(g.gc.find(".//altitudeUnits").getparent())
    assert g.altitude_units() is None


# pylint: disable=protected-access
def test__convert_to_meters(geocov):
    """Test geographicCoverage _convert_to_meters method

    This method should convert the altitude values to meters if they are not
    already in meters. If the altitude units are not specified, the method
    should return None, which is the default value returned by the
    altitude_minimum and altitude_maximum methods. Because this is a method
    of the geographicCoverage class, it is not possible to test it directly
    so we use an instance of geographicCoverage to access the method for
    testing.
    """
    g = geocov[0]
    # Case when no altitude or units are specified in the geographicCoverage
    assert g._convert_to_meters(x=None, from_units=None) is None
    # Case when altitude is specified but no units are specified. Should return value as is.
    assert g._convert_to_meters(x=10, from_units=None) == 10
    # Case when altitude is not specified but units are.
    assert g._convert_to_meters(x=None, from_units="meters") is None
    # Case when altitude is specified and units are specified. Should convert to meters.
    assert g._convert_to_meters(x=10, from_units="foot") == 3.048
