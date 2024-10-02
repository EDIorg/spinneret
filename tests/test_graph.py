"""Test graph code"""

from os import listdir
import importlib
from rdflib import Graph, Literal, URIRef
from spinneret.graph import (
    create_graph,
    convert_keyword_url_to_uri,
    convert_variable_property_id_to_uri,
    convert_variable_measurement_technique_to_uri,
    convert_variable_unit_code_to_uri,
    convert_license_to_uri,
)


def test_create_graph():
    """Test create_graph"""

    # Load_metadata
    data_dir = str(importlib.resources.files("spinneret.data")) + "/jsonld"
    metadata_files = [data_dir + "/" + f for f in listdir(data_dir)]
    res = create_graph(metadata_files=metadata_files)
    assert res is not None
    assert len(res) == 650  # based on current metadata files

    # Load_vocabularies
    data_dir = "tests/data/vocab"
    vocabulary_files = [data_dir + "/" + f for f in listdir(data_dir)]
    res = create_graph(vocabulary_files=vocabulary_files)
    assert res is not None
    assert len(res) == 18  # based on current vocabulary files

    # Load both metadata and vocabularies
    res = create_graph(metadata_files=metadata_files, vocabulary_files=vocabulary_files)
    assert res is not None
    assert len(res) == 668  # based on current metadata and vocabulary files


def test_convert_keyword_url_to_uri_converts_if_url():
    """Test that the convert_keyword_url_to_uri function applies the conversion
    if the value looks like a URL"""

    test_data = """
    {
        "@context": {"@vocab": "https://schema.org/"},
        "@type": "Dataset",
        "keywords": [
            {
                "@type": "DefinedTerm",
                "url": "http://purl.obolibrary.org/obo/CHEBI_33284"
            }
        ]
    }
    """
    g = Graph()
    g.parse(data=test_data, format="json-ld")

    g = convert_keyword_url_to_uri(g)
    query = """
        PREFIX schema: <https://schema.org/>

        SELECT ?url
        WHERE {
          ?dataset schema:keywords ?term .
          ?term a schema:DefinedTerm .
          ?term schema:url ?url .
        }
        """
    results = g.query(query)
    for result in results:
        assert isinstance(result[0], URIRef)  # is now a URIRef


def test_convert_keyword_url_to_uri_does_not_convert_if_text():
    """Test that the convert_keyword_url_to_uri function does not apply the
    conversion if the value does not look like a URL"""

    test_data = """
    {
        "@context": {"@vocab": "https://schema.org/"},
        "@type": "Dataset",
        "keywords": [
            {
                "@type": "DefinedTerm",
                "url": "not URL formatted text"
            }
        ]
    }
    """
    g = Graph()
    g.parse(data=test_data, format="json-ld")

    g = convert_keyword_url_to_uri(g)
    query = """
    PREFIX schema: <https://schema.org/>

    SELECT ?url
    WHERE {
      ?dataset schema:keywords ?term .
      ?term a schema:DefinedTerm .
      ?term schema:url ?url .
    }
    """
    results = g.query(query)
    for result in results:
        assert isinstance(result[0], Literal)  # is still a Literal


def test_convert_variable_property_id_to_uri_converts_if_url():
    """Test that the convert_variable_property_id_to_uri function applies the
    conversion if the value looks like a URL"""

    test_data = """
    {
        "@context": {"@vocab": "https://schema.org/"},
        "@type": "Dataset",
        "variableMeasured": [
            {
                "@type": "PropertyValue",
                "propertyID": "http://purl.dataone.org/odo/ECSO_00002566"
            }
        ]
    }
    """
    g = Graph()
    g.parse(data=test_data, format="json-ld")

    g = convert_variable_property_id_to_uri(g)
    query = """
    PREFIX schema: <https://schema.org/>

    SELECT ?propertyID
    WHERE {
      ?dataset schema:variableMeasured ?term .
      ?term a schema:PropertyValue .
      ?term schema:propertyID ?propertyID .
    }
    """
    results = g.query(query)
    for result in results:
        assert isinstance(result[0], URIRef)  # is now a URIRef


def test_convert_variable_property_id_to_uri_does_not_convert_if_text():
    """Test that the convert_variable_property_id_to_uri function does not
    apply the conversion if the value does not look like a URL"""

    test_data = """
    {
        "@context": {"@vocab": "https://schema.org/"},
        "@type": "Dataset",
        "variableMeasured": [
            {
                "@type": "PropertyValue",
                "propertyID": "not URL formatted text"
            }
        ]
    }
    """
    g = Graph()
    g.parse(data=test_data, format="json-ld")

    g = convert_variable_property_id_to_uri(g)
    query = """
    PREFIX schema: <https://schema.org/>

    SELECT ?propertyID
    WHERE {
      ?dataset schema:variableMeasured ?term .
      ?term a schema:PropertyValue .
      ?term schema:propertyID ?propertyID .
    }
    """
    results = g.query(query)
    for result in results:
        assert isinstance(result[0], Literal)  # is now a URIRef


def test_convert_variable_measurement_technique_to_uri_converts_if_url():
    """Test that the convert_variable_measurement_technique_to_uri function
    applies the conversion if the value looks like a URL"""

    test_data = """
    {
        "@context": {"@vocab": "https://schema.org/"},
        "@type": "Dataset",
        "variableMeasured": [
            {
                "@type": "PropertyValue",
                "measurementTechnique": "http://example.org/method/8675309"
            }
        ]
    }
    """
    g = Graph()
    g.parse(data=test_data, format="json-ld")

    g = convert_variable_measurement_technique_to_uri(g)
    query = """
    PREFIX schema: <https://schema.org/>

    SELECT ?value
    WHERE {
      ?dataset schema:variableMeasured ?term .
      ?term a schema:PropertyValue .
      ?term schema:measurementTechnique ?value .
    }
    """
    results = g.query(query)
    for result in results:
        assert isinstance(result[0], URIRef)  # is now a URIRef


def test_convert_variable_measurement_technique_to_uri_does_not_convert_if_text():
    """Test that the convert_variable_measurement_technique_to_uri function
    does not apply the conversion if the value does not look like a URL"""

    test_data = """
    {
        "@context": {"@vocab": "https://schema.org/"},
        "@type": "Dataset",
        "variableMeasured": [
            {
                "@type": "PropertyValue",
                "measurementTechnique": "not URL formatted text"
            }
        ]
    }
    """
    g = Graph()
    g.parse(data=test_data, format="json-ld")

    g = convert_variable_measurement_technique_to_uri(g)
    query = """
    PREFIX schema: <https://schema.org/>

    SELECT ?value
    WHERE {
      ?dataset schema:variableMeasured ?term .
      ?term a schema:PropertyValue .
      ?term schema:measurementTechnique ?value .
    }
    """
    results = g.query(query)
    for result in results:
        assert isinstance(result[0], Literal)  # is still a Literal


def test_convert_variable_unit_code_to_uri_converts_if_url():
    """Test that the convert_variable_unit_code_to_uri function applies the
    conversion if the value looks like a URL"""
    test_data = """
    {
        "@context": {"@vocab": "https://schema.org/"},
        "@type": "Dataset",
        "variableMeasured": [
            {
                "@type": "PropertyValue",
                "unitCode": "http://example.org/unit/2112"
            }
        ]
    }
    """
    g = Graph()
    g.parse(data=test_data, format="json-ld")

    g = convert_variable_unit_code_to_uri(g)
    query = """
    PREFIX schema: <https://schema.org/>

    SELECT ?value
    WHERE {
      ?dataset schema:variableMeasured ?term .
      ?term a schema:PropertyValue .
      ?term schema:unitCode ?value .
    }
    """
    results = g.query(query)
    for result in results:
        assert isinstance(result[0], URIRef)  # is now a URIRef


def test_convert_variable_unit_code_to_uri_does_not_convert_if_text():
    """Test that the convert_variable_unit_code_to_uri function does not apply
    the conversion if the value does not look like a URL"""
    test_data = """
    {
        "@context": {"@vocab": "https://schema.org/"},
        "@type": "Dataset",
        "variableMeasured": [
            {
                "@type": "PropertyValue",
                "unitCode": "not URL formatted text"
            }
        ]
    }
    """
    g = Graph()
    g.parse(data=test_data, format="json-ld")

    g = convert_variable_unit_code_to_uri(g)
    query = """
    PREFIX schema: <https://schema.org/>

    SELECT ?value
    WHERE {
      ?dataset schema:variableMeasured ?term .
      ?term a schema:PropertyValue .
      ?term schema:unitCode ?value .
    }
    """
    results = g.query(query)
    for result in results:
        assert isinstance(result[0], Literal)  # is still a Literal


def test_convert_license_to_uri_converts_if_url():
    """Test that the convert_license_to_uri function applies the conversion if
    the value looks like a URL"""
    test_data = """
        {
            "@context": {"@vocab": "https://schema.org/"},
            "@type": "Dataset",
            "license": "http://spdx.org/licenses/CC0-1.0"
        }
        """
    g = Graph()
    g.parse(data=test_data, format="json-ld")

    g = convert_license_to_uri(g)
    query = """
    PREFIX schema: <https://schema.org/>

    SELECT ?value
    WHERE {
      ?dataset schema:license ?value .
    }
    """
    results = g.query(query)
    for result in results:
        assert isinstance(result[0], URIRef)  # is now a URIRef


def test_convert_license_to_uri_does_not_convert_if_text():
    """Test that the convert_license_to_uri function does not apply the
    conversion if the value does not look like a URL"""
    test_data = """
        {
            "@context": {"@vocab": "https://schema.org/"},
            "@type": "Dataset",
            "license": "not URL formatted text"
        }
        """
    g = Graph()
    g.parse(data=test_data, format="json-ld")

    g = convert_license_to_uri(g)
    query = """
    PREFIX schema: <https://schema.org/>

    SELECT ?value
    WHERE {
      ?dataset schema:license ?value .
    }
    """
    results = g.query(query)
    for result in results:
        assert isinstance(result[0], Literal)  # is still a Literal
