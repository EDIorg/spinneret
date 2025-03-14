"""EML metadata related operations"""
import json
from math import isnan
from lxml import etree
import geopandas as gpd


def get_geographic_coverage(eml):
    """Get geographicCoverage elements from EML metadata

    Parameters
    ----------
    eml : str
        Path to EML metadata file

    Returns
    -------
    list : GeographicCoverage
        List of GeographicCoverage instances
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
    """geographicCoverage related operations"""

    def __init__(self, gc):
        self.gc = gc

    def description(self):
        """Get geographicDescription element from geographicCoverage

        Returns
        -------
        str : description
            geographicDescription element

        Examples
        --------
        >>> from spinneret import eml
        >>> res = eml.get_geographic_coverage(
        ...     eml="src/spinneret/data/eml/edi.1.1.xml"
        ... )
        >>> res[0].description()
        """
        try:
            return self.gc.findtext(".//geographicDescription")
        except TypeError:
            return None

    def west(self):
        """Get westBoundingCoordinate element from geographicCoverage

        Returns
        -------
        float : west
            westBoundingCoordinate element

        Examples
        --------
        >>> from spinneret import eml
        >>> res = eml.get_geographic_coverage(
        ...     eml="src/spinneret/data/eml/edi.1.1.xml"
        ... )
        >>> res[0].westBoundingCoordinate()
        """
        try:
            return float(self.gc.findtext(".//westBoundingCoordinate"))
        except TypeError:
            return None

    def east(self):
        """Get eastBoundingCoordinate element from geographicCoverage

        Returns
        -------
        float : east
            eastBoundingCoordinate element

        Examples
        --------
        >>> from spinneret import eml
        >>> res = eml.get_geographic_coverage(
        ...     eml="src/spinneret/data/eml/edi.1.1.xml"
        ... )
        >>> res[0].east()
        """
        try:
            return float(self.gc.findtext(".//eastBoundingCoordinate"))
        except TypeError:
            return None

    def north(self):
        """Get northBoundingCoordinate element from geographicCoverage

        Returns
        -------
        float : north
            northBoundingCoordinate element

        Examples
        --------
        >>> from spinneret import eml
        >>> res = eml.get_geographic_coverage(
        ...     eml="src/spinneret/data/eml/edi.1.1.xml"
        ... )
        >>> res[0].north()
        """
        try:
            return float(self.gc.findtext(".//northBoundingCoordinate"))
        except TypeError:
            return None

    def south(self):
        """Get southBoundingCoordinate element from geographicCoverage

        Returns
        -------
        float : south
            southBoundingCoordinate element

        Examples
        --------
        >>> from spinneret import eml
        >>> res = eml.get_geographic_coverage(
        ...     eml="src/spinneret/data/eml/edi.1.1.xml"
        ... )
        >>> res[0].south()
        """
        try:
            return float(self.gc.findtext(".//southBoundingCoordinate"))
        except TypeError:
            return None

    def altitude_minimum(self, to_meters=False):
        """Get altitudeMinimum element from geographicCoverage

        Parameters
        ----------
        to_meters : bool
            Convert to meters?

        Returns
        -------
        float : altitude_minimum
            altitudeMinimum element

        Notes
        -----
        A conversion to meters is based on the value retrieved from the
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

    def altitude_maximum(self, to_meters=False):
        """Get altitudeMaximum element from geographicCoverage

        Parameters
        ----------
        to_meters : bool
            Convert to meters?

        Returns
        -------
        float : altitude_maximum
            altitudeMaximum element

        Notes
        -----
        A conversion to meters is based on the value retrieved from the
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

    def altitude_units(self):
        try:
            return self.gc.findtext(".//altitudeUnits")
        except TypeError:
            return None

    def outer_gring(self):
        """Get datasetGPolygonOuterGRing/gRing element from geographicCoverage

        Returns
        -------
        str : outer_gring
            datasetGPolygonOuterGRing/gRing element

        Examples
        --------
        >>> from spinneret import eml
        >>> res = eml.get_geographic_coverage(
        ...     eml="src/spinneret/data/eml/edi.1.1.xml"
        ... )
        >>> res[0].outer_gring()
        """
        try:
            return self.gc.findtext(".//datasetGPolygonOuterGRing/gRing")
        except TypeError:
            return None

    def exclusion_gring(self):
        """Get datasetGPolygonExclusionGRing/gRing element from
        geographicCoverage

        Returns
        -------
        str : exclusion_gring
            datasetGPolygonExclusionGRing/gRing element

        Examples
        --------
        >>> from spinneret import eml
        >>> res = eml.get_geographic_coverage(
        ...     eml="src/spinneret/data/eml/edi.1.1.xml"
        ... )
        >>> res[0].exclusion_gring()
        """
        try:
            return self.gc.findtext(".//datasetGPolygonExclusionGRing/gRing")
        except TypeError:
            return None

    def geom_type(self, schema="eml"):
        """Get geometry type from geographicCoverage

        Parameters
        ----------
        schema : str
            Schema dialect to use when returning values, either "eml" or "esri"

        Returns
        -------
        str : geometry type
            geometry type as "polygon", "point", or "envelope" for
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

    def to_esri_geometry(self):
        """Convert geographicCoverage to ESRI JSON geometry

        Returns
        -------
        str : ESRI JSON geometry
            ESRI JSON geometry type as "polygon", "point", or "envelope"

        Notes
        -----
        The logic here presumes that if a polygon is listed, it is the true
        feature of interest, rather than the associated boundingCoordinates,
        which are required to be listed by the EML spec alongside all polygon
        listings.

        Geographic coverage latitude and longitude are assumed to be in the
        spatial reference system of WKID 4326 and are inserted into the ESRI
        geometry as x and y values. Geographic coverages with altitudes and
        associated units are converted to units of meters and added to the ESRI
        geometry as z values.

        Geographic coverages that are point locations, as indicated by their
        bounding box latitude min and max values and longitude min and max
        values being equivalent, are converted to ESRI envelopes rather than
        ESRI points, because the envelope geometry type is more expressive and
        handles more usecases than the point geometry alone. Furthermore, point
        locations represented as envelope geometries produce the same results
        as if the point of location was represented as a point geometry.

        Examples
        --------
        >>> from spinneret import eml
        >>> res = eml.get_geographic_coverage(
        ...     eml="src/spinneret/data/eml/edi.1.1.xml"
        ... )
        >>> res[0].to_esri_geometry()
        >>> res[1].to_esri_geometry()
        >>> res[2].to_esri_geometry()
        """
        if self.geom_type() == "polygon":
            return self._to_esri_polygon()
        if self.geom_type() == "point":
            return (
                self._to_esri_envelope()
            )  # Envelopes are more expressive and behave the same as point geometries, so us envelopes
        if self.geom_type() == "envelope":
            return self._to_esri_envelope()
        return None

    def _to_esri_envelope(self):
        """Convert boundingCoordinates to ESRI JSON envelope geometry

        Returns
        -------
        str : ESRI JSON envelope geometry
            ESRI JSON envelope geometry

        Notes
        -----
        Defaulting to WGS84 because the EML spec does not specify a CRS and
        notes the coordinates are meant to convey general information.
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

    def _to_esri_polygon(self):
        """Convert datasetGPolygon to ESRI JSON polygon geometry

        Returns
        -------
        str : ESRI JSON polygon geometry
            ESRI JSON polygon geometry

        Notes
        -----
        Defaulting to WGS84 because the EML spec does not specify a CRS and
        notes the coordinates are meant to convey general information.
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
            # TODO Ensure that the outer ring is oriented clockwise and the
            #  inner ring is oriented counter-clockwise
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
    def _convert_to_meters(x, from_units):
        """Convert an elevation from a given unit of measurement to meters.

        Parameters
        ----------
        x : float
            Value to convert.
        from_units : str
            Units to convert from. This must be one of: meter, decimeter,
            dekameter, hectometer, kilometer, megameter, Foot_US, foot,
            Foot_Gold_Coast, fathom, nauticalMile, yard, Yard_Indian,
            Link_Clarke, Yard_Sears, mile.

        Returns
        -------
        float : in units of meters
        """
        # TODO Warn if x is a non-nan float and the units are empty. This indicates that
        #  the value has no units and results derived from subsequent use of the value
        #  may be incorrect.
        if x is None:
            x = float("NaN")
        conversion_factors = _load_conversion_factors()
        conversion_factor = conversion_factors.get(from_units, float("NaN"))
        if not isnan(
            conversion_factor
        ):  # Apply the conversion factor if from_units is a valid unit of measurement otherwise return the length value as is
            x = x * conversion_factors.get(from_units, float("NaN"))
        if isnan(
            x
        ):  # Convert back to None, which is the NULL type returned by altitude_minimum and altitude_maximum
            x = None
        return x


def _load_conversion_factors():
    """Load conversion factors

    Returns
    -------
    dict : conversion factors
        Dictionary of conversion factors for converting from common units of
        length to meters.
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


if __name__ == "__main__":
    geocov = get_geographic_coverage(eml="data/eml/edi.1.1.xml")
    for item in geocov:
        print(item.to_esri_geometry())
