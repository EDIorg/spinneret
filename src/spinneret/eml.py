"""EML metadata related operations"""

import json
import warnings
from math import isnan
from typing import List, Union
from lxml import etree


def get_geographic_coverage(eml: str) -> List["GeographicCoverage"]:
    """Get GeographicCoverage objects from EML metadata

    :param eml: path to EML metadata
    :return: list of geographicCoverage objects
    """
    xml = etree.parse(eml)
    gc = xml.xpath(".//geographicCoverage")
    if len(gc) == 0:
        return None
    res = []
    for item in gc:
        res.append(GeographicCoverage(item))
    return res


class GeographicCoverage:
    """GeographicCoverage class"""

    def __init__(self, gc):
        self.gc = gc

    def description(self) -> Union[str | None]:
        """Get geographicDescription element value from geographicCoverage

        :return: geographicDescription
        """
        try:
            return self.gc.findtext(".//geographicDescription")
        except TypeError:
            return None

    def west(self) -> Union[float | None]:
        """
        Get westBoundingCoordinate element value from geographicCoverage

        :return: westBoundingCoordinate
        """
        try:
            return float(self.gc.findtext(".//westBoundingCoordinate"))
        except TypeError:
            return None

    def east(self) -> Union[float | None]:
        """Get eastBoundingCoordinate element value from geographicCoverage

        :return: eastBoundingCoordinate
        """
        try:
            return float(self.gc.findtext(".//eastBoundingCoordinate"))
        except TypeError:
            return None

    def north(self) -> Union[float | None]:
        """Get northBoundingCoordinate element value from geographicCoverage

        :return: northBoundingCoordinate
        """
        try:
            return float(self.gc.findtext(".//northBoundingCoordinate"))
        except TypeError:
            return None

    def south(self) -> Union[float | None]:
        """Get southBoundingCoordinate element value from geographicCoverage

        :return: southBoundingCoordinate
        """
        try:
            return float(self.gc.findtext(".//southBoundingCoordinate"))
        except TypeError:
            return None

    def altitude_minimum(self, to_meters=False) -> Union[float | None]:
        """Get altitudeMinimum element value from geographicCoverage

        :param to_meters: Convert to meters?
        :return: altitudeMinimum
        :notes: A conversion to meters is based on the value retrieved from the
            altitudeUnits element of the geographic coverage, and a conversion
            table from the EML specification. If the altitudeUnits element is
            not present, and the to_meters parameter is True, then the altitude
            value is returned as-is and a warning issued.
        """
        try:
            res = float(self.gc.findtext(".//altitudeMinimum"))
        except TypeError:
            res = None
        if to_meters is True:
            res = self._convert_to_meters(x=res, from_units=self.altitude_units())
        return res

    def altitude_maximum(self, to_meters=False) -> Union[float | None]:
        """Get altitudeMaximum element value from geographicCoverage

        :param to_meters: Convert to meters?
        :return: altitudeMaximum
        :notes: A conversion to meters is based on the value retrieved from the
            altitudeUnits element of the geographic coverage, and a conversion
            table from the EML specification. If the altitudeUnits element is
            not present, and the to_meters parameter is True, then the altitude
            value is returned as-is and a warning issued.
        """
        try:
            res = float(self.gc.findtext(".//altitudeMaximum"))
        except TypeError:
            res = None
        if to_meters is True:
            res = self._convert_to_meters(x=res, from_units=self.altitude_units())
        return res

    def altitude_units(self) -> Union[str | None]:
        """Get altitudeUnits element value from geographicCoverage

        :return: altitudeUnits
        """
        try:
            return self.gc.findtext(".//altitudeUnits")
        except TypeError:
            return None

    def outer_gring(self) -> Union[str | None]:
        """Get datasetGPolygonOuterGRing/gRing element value from
        geographicCoverage

        :return: datasetGPolygonOuterGRing/gRing element
        """
        try:
            return self.gc.findtext(".//datasetGPolygonOuterGRing/gRing")
        except TypeError:
            return None

    def exclusion_gring(self) -> Union[str | None]:
        """Get datasetGPolygonExclusionGRing/gRing element value from
        geographicCoverage

        :return: datasetGPolygonExclusionGRing/gRing
        """
        try:
            return self.gc.findtext(".//datasetGPolygonExclusionGRing/gRing")
        except TypeError:
            return None

    def geom_type(self, schema="eml") -> Union[str | None]:
        """Get geometry type from geographicCoverage

        :param: Schema dialect to use when returning values, either "eml" or
            "esri"
        :return: geometry type as "polygon", "point", or "envelope" for
            `schema="eml"`, or "esriGeometryPolygon", "esriGeometryPoint", or
            "esriGeometryEnvelope" for `schema="esri"`
        """
        if self.gc.find(".//datasetGPolygon") is not None:
            if schema == "eml":
                return "polygon"
            return "esriGeometryPolygon"
        if self.gc.find(".//boundingCoordinates") is not None:
            if self.west() == self.east() and self.north() == self.south():
                if schema == "eml":
                    res = "point"
                else:
                    res = "esriGeometryPoint"
                return res
            if schema == "eml":
                res = "envelope"
            else:
                res = "esriGeometryEnvelope"
            return res
        return None

    def to_esri_geometry(self) -> Union[str | None]:
        """Convert geographicCoverage to ESRI JSON geometry

        :return: ESRI JSON geometry type as "polygon", "point", or "envelope"

        :notes: The logic here presumes that if a polygon is listed, it is the
            true feature of interest, rather than the associated
            boundingCoordinates, which are required to be listed by the EML
            spec alongside all polygon listings.

            Geographic coverage latitude and longitude are assumed to be in the
            spatial reference system of WKID 4326 and are inserted into the
            ESRI geometry as x and y values. Geographic coverages with
            altitudes and associated units are converted to units of meters and
            added to the ESRI geometry as z values.

            Geographic coverages that are point locations, as indicated by
            their bounding box latitude min and max values and longitude min
            and max values being equivalent, are converted to ESRI envelopes
            rather than ESRI points, because the envelope geometry type is more
            expressive and handles more usecases than the point geometry alone.
            Furthermore, point locations represented as envelope geometries
            produce the same results as if the point of location was
            represented as a point geometry.
        """
        if self.geom_type() == "polygon":
            return self._to_esri_polygon()
        if self.geom_type() == "point":
            return (
                self._to_esri_envelope()
            )  # Envelopes are more expressive and behave the same as point
            # geometries, so us envelopes
        if self.geom_type() == "envelope":
            return self._to_esri_envelope()
        return None

    def _to_esri_envelope(self) -> str:
        """Convert boundingCoordinates to ESRI JSON envelope geometry

        :return: ESRI JSON envelope geometry
        :notes: Defaulting to WGS84 because the EML spec does not specify a
        CRS and notes the coordinates are meant to convey general information.
        """
        altitude_minimum = self.altitude_minimum(to_meters=True)
        altitude_maximum = self.altitude_maximum(to_meters=True)
        res = {
            "xmin": self.west(),
            "ymin": self.south(),
            "xmax": self.east(),
            "ymax": self.north(),
            "zmin": altitude_minimum,
            "zmax": altitude_maximum,
            "spatialReference": {"wkid": 4326},
        }
        return json.dumps(res)

    def _to_esri_polygon(self) -> str:
        """Convert datasetGPolygon to ESRI JSON polygon geometry

        :return: ESRI JSON polygon geometry
        :notes: Defaulting to WGS84 because the EML spec does not specify a
        CRS and notes the coordinates are meant to convey general information.
        """

        def _format_ring(gring):
            # Reformat the string of coordinates into a list of lists
            ring = []
            for item in gring.split():
                x = item.split(",")
                # Try to convert the coordinates to floats. The EML spec does
                # not enforce strictly numeric values.
                try:
                    ring.append([float(x[0]), float(x[1])])
                except TypeError:
                    ring.append([x[0], x[1]])
            # Ensure that the first and last points are the same
            if ring[0] != ring[-1]:
                ring.append(ring[0])
            return ring

        if self.outer_gring() is not None:
            ring = _format_ring(self.outer_gring())
            res = {"rings": [ring], "spatialReference": {"wkid": 4326}}
            if self.exclusion_gring() is not None:
                ring = _format_ring(self.exclusion_gring())
                res["rings"].append(ring)
            return json.dumps(res)
        return None

    @staticmethod
    def _convert_to_meters(x, from_units) -> Union[float | None]:
        """Convert an elevation from a given unit of measurement to meters.

        :param x: value to convert
        :param from_units: Units to convert from. This must be one of: meter,
            decimeter, dekameter, hectometer, kilometer, megameter, Foot_US,
            foot, Foot_Gold_Coast, fathom, nauticalMile, yard, Yard_Indian,
            Link_Clarke, Yard_Sears, mile.
        :return: value in meters
        """
        if x is None:
            x = float("NaN")
        conversion_factors = _load_conversion_factors()
        conversion_factor = conversion_factors.get(from_units, float("NaN"))
        if not isnan(
            conversion_factor
        ):  # Apply the conversion factor if from_units is a valid unit of
            # measurement otherwise return the length value as is
            x = x * conversion_factors.get(from_units, float("NaN"))
        if isnan(x):  # Convert back to None, which is the NULL type returned by
            # altitude_minimum and altitude_maximum
            x = None
        return x

    def to_geojson_geometry(self) -> Union[str | None]:
        """Convert geographicCoverage to GeoJSON geometry

        :return: GeoJSON geometry type as "polygon" or "point"

        :notes: The logic here presumes that if a polygon is listed, it is the
            true feature of interest, rather than the associated
            boundingCoordinates, which are required to be listed by the EML
            spec alongside all polygon listings.

            Geographic coverage latitude and longitude are assumed to be in the
            spatial reference system of WKID 4326 and are inserted into the
            GeoJSON geometry as x and y values. Geographic coverages with
            altitudes and associated units are converted to units of meters and
            added to the GeoJSON geometry as z values.

            Geographic coverages that are point locations, as indicated by
            their bounding box latitude min and max values and longitude min
            and max values being equivalent, are converted to GeoJSON points.
        """
        if self.geom_type() == "polygon" or self.geom_type() == "envelope":
            return self._to_geojson_polygon()
        if self.geom_type() == "point":
            return self._to_geojson_point()
        return None

    def _to_geojson_polygon(self) -> str:
        """Convert EML polygon or envelope to GeoJSON polygon geometry"""
        if self.geom_type() == "envelope":
            z = self._average_altitudes()
            coordinates = [
                [self.west(), self.south(), z],
                [self.east(), self.south(), z],
                [self.east(), self.north(), z],
                [self.west(), self.north(), z],
                [self.west(), self.south(), z],
            ]
            coordinates = [list(filter(None, item)) for item in coordinates]
            res = {
                "type": "Polygon",
                "coordinates": [coordinates],
            }
            return json.dumps(res)

        if self.geom_type() == "polygon":

            def _format_ring(gring):
                # Reformat the string of coordinates into a list of lists
                ring = []
                z = self._average_altitudes()
                for item in gring.split():
                    x = item.split(",")
                    # Try to convert the coordinates to floats. The EML spec does
                    # not enforce strictly numeric values.
                    try:
                        ring.append([float(x[0]), float(x[1]), z])
                    except TypeError:
                        ring.append([x[0], x[1], z])
                # Ensure that the first and last points are the same
                if ring[0] != ring[-1]:
                    ring.append(ring[0])
                # Remove None values to comply with GeoJSON spec
                ring = [list(filter(None, item)) for item in ring]
                return ring

            if self.outer_gring() is not None:
                ring = _format_ring(self.outer_gring())  # counter-clockwise
                res = {"type": "Polygon", "coordinates": [ring]}
                # if self.exclusion_gring() is not None:
                #     ring = _format_ring(self.exclusion_gring())  # clockwise
                #     res["coordinates"].append(ring)
                return json.dumps(res)

        return None

    def _to_geojson_point(self) -> Union[str | None]:
        """Convert EML point to GeoJSON point geometry"""
        if self.geom_type() != "point":
            return None
        z = self._average_altitudes()
        coordinates = [self.west(), self.north(), z]
        # Remove z values that are None to comply with GeoJSON spec
        coordinates = list(filter(None, coordinates))
        res = {"type": "Point", "coordinates": coordinates}
        return json.dumps(res)

    def _average_altitudes(self) -> Union[float | None]:
        """Average the minimum and maximum altitudes

        :return: average altitude
        :notes: GeoJSON doesn't support a range of z values, so we'll just use
            the average of the minimum and maximum values.
        """
        try:
            altitude_minimum = self.altitude_minimum(to_meters=True)
            altitude_maximum = self.altitude_maximum(to_meters=True)
            z = (altitude_minimum + altitude_maximum) / 2
            if altitude_minimum != altitude_maximum:
                warnings.warn(
                    "Altitude minimum and maximum are different. Using "
                    "average value."
                )
        except TypeError:
            z = None
        return z


def _load_conversion_factors() -> dict:
    """Load conversion factors

    :return: Dictionary of conversion factors for converting from common units
        of length to meters.
    """
    conversion_factors = {
        "meter": 1,
        "decimeter": 1e-1,
        "dekameter": 1e1,
        "hectometer": 1e2,
        "kilometer": 1e3,
        "megameter": 1e6,
        "Foot_US": 0.3048006,
        "foot": 0.3048,
        "Foot_Gold_Coast": 0.3047997,
        "fathom": 1.8288,
        "nauticalMile": 1852,
        "yard": 0.9144,
        "Yard_Indian": 0.914398530744440774,
        "Link_Clarke": 0.2011661949,
        "Yard_Sears": 0.91439841461602867,
        "mile": 1609.344,
    }
    return conversion_factors
