"""The graph module"""

from rdflib import Graph
from rdflib.util import guess_format


def create_graph(metadata_files: list = None, vocabulary_files: list = None) -> Graph:
    """
    :param metadata_files: List of file paths to metadata in JSON-LD format
    :param vocabulary_files: List of file paths to vocabularies
    :returns: Graph of the combined metadata and vocabularies
    :notes: If no vocabulary files are provided, only the metadata are loaded
        into the graph, and vice versa if no metadata files are provided.

        Vocabulary formats are identified by the file extension according
        to `rdflib.util.guess_format`
    """
    g = Graph()

    # Load metadata
    if metadata_files is not None:
        for filename in metadata_files:
            g.parse(filename, format="json-ld")

    # Load vocabularies
    if vocabulary_files is not None:
        for filename in vocabulary_files:
            g.parse(filename, format=guess_format(filename))

    # Some string literals should be converted to URIRefs to create linked
    # data with vocabularies. These are often cases where SOSO conventions
    # recommend connecting the value to an object property (e.g. `url`) rather
    # than the object @id. The following code makes these conversions based on
    # where vocabulary URIs can be used in SOSO markup.
    g = convert_keyword_url_to_uri(g)
    g = convert_variable_property_id_to_uri(g)
    g = convert_variable_measurement_technique_to_uri(g)
    g = convert_variable_unit_code_to_uri(g)
    g = convert_license_to_uri(g)

    return g


def convert_keyword_url_to_uri(graph: Graph) -> Graph:
    """
    :param graph: Graph of metadata and vocabularies
    :returns: Graph with keyword URLs converted to URIs
    :notes: Converts values of `schema:keyword/schema:DefinedTerm/schema:url`
        to URI references if the value appears to be a URL.
    """
    update_request = """
    PREFIX schema: <https://schema.org/>

    DELETE {
        ?term schema:url ?value .
    }
    INSERT {
        ?term schema:url ?newURI .
    }
    WHERE {
        ?dataset schema:keywords ?term .
        ?term a schema:DefinedTerm .
        ?term schema:url ?value .
        FILTER (isLiteral(?value) && REGEX(?value, "^https?://", "i")) .
        BIND (URI(?value) AS ?newURI)
    }
    """
    graph.update(update_request)
    return graph


def convert_variable_property_id_to_uri(graph: Graph) -> Graph:
    """
    :param graph: Graph of metadata and vocabularies
    :returns: Graph with variable property IDs converted to URIs
    :notes: Converts values of `schema:variableMeasured/schema:PropertyValue/
        schema:propertyID` to URI references if the value appears to be a URL.
    """
    update_request = """
    PREFIX schema: <https://schema.org/>

    DELETE {
        ?term schema:propertyID ?value .
    }
    INSERT {
        ?term schema:propertyID ?newURI .
    }
    WHERE {
        ?dataset schema:variableMeasured ?term .
        ?term a schema:PropertyValue .
        ?term schema:propertyID ?value .
        FILTER (isLiteral(?value) && REGEX(?value, "^https?://", "i")) .
        BIND (URI(?value) AS ?newURI)
    }
    """
    graph.update(update_request)
    return graph


def convert_variable_measurement_technique_to_uri(graph: Graph) -> Graph:
    """
    :param graph: Graph of metadata and vocabularies
    :returns: Graph with variable measurement techniques converted to URIs
    :notes: Converts values of `schema:variableMeasured/schema:PropertyValue/
        schema:measurementTechnique` to URI references if the value appears to
        be a URL.
    """
    update_request = """
    PREFIX schema: <https://schema.org/>

    DELETE {
        ?term schema:measurementTechnique ?value .
    }
    INSERT {
        ?term schema:measurementTechnique ?newURI .
    }
    WHERE {
        ?dataset schema:variableMeasured ?term .
        ?term a schema:PropertyValue .
        ?term schema:measurementTechnique ?value .
        FILTER (isLiteral(?value) && REGEX(?value, "^https?://", "i")) .
        BIND (URI(?value) AS ?newURI)
    }
    """
    graph.update(update_request)
    return graph


def convert_variable_unit_code_to_uri(graph: Graph) -> Graph:
    """
    :param graph: Graph of metadata and vocabularies
    :returns: Graph with variable unit codes converted to URIs
    :notes: Converts values of `schema:variableMeasured/schema:PropertyValue/
        schema:unitCode` to URI references if the value appears to be a URL.
    """
    update_request = """
    PREFIX schema: <https://schema.org/>

    DELETE {
        ?term schema:unitCode ?value .
    }
    INSERT {
        ?term schema:unitCode ?newURI .
    }
    WHERE {
        ?dataset schema:variableMeasured ?term .
        ?term a schema:PropertyValue .
        ?term schema:unitCode ?value .
        FILTER (isLiteral(?value) && REGEX(?value, "^https?://", "i")) .
        BIND (URI(?value) AS ?newURI)
    }
    """
    graph.update(update_request)
    return graph


def convert_license_to_uri(graph: Graph) -> Graph:
    """
    :param graph: Graph of metadata and vocabularies
    :returns: Graph with licenses converted to URIs
    :notes: Converts values of `schema:license` to URI references if the value
        appears to be a URL.
    """
    update_request = """
    PREFIX schema: <https://schema.org/>

    DELETE {
        ?dataset schema:license ?value .
    }
    INSERT {
        ?dataset schema:license ?newURI .
    }
    WHERE {
        ?dataset schema:license ?value .
        FILTER (isLiteral(?value) && REGEX(?value, "^https?://", "i")) .
        BIND (URI(?value) AS ?newURI)
    }
    """
    graph.update(update_request)
    return graph


if __name__ == "__main__":
    # Example usage
    WORKING_DIR = "/Users/csmith/Data/soso/all_edi_test_results"
    list_of_files = ["edi.1.1.json", "edi.3.10.json", "edi.5.5.json"]
    working_files = [WORKING_DIR + "/" + f for f in list_of_files]
    res = create_graph(metadata_files=working_files)

    # # Full example
    # working_dir = "/Users/csmith/Data/soso/all_edi_test_results"
    # import os
    # files = os.listdir(working_dir)
    # # Filter only JSON-LD files and Get full file paths
    # files = [f for f in files if f.endswith(".json")]
    # working_files = [working_dir + "/" + f for f in files]
    # # # Randomly choose 100 files
    # # import random
    # # working_files = random.choices(working_files, k=1000)
    # # Create full graph
    # g = create_graph(metadata_files=working_files)

    # # Serialize to file
    # output_file = "/Users/csmith/Data/soso/all_edi_test_graph/combined.ttl"
    # g.serialize(destination=output_file, format="turtle")

    # # Example SPARQL query
    # import rdflib
    # from rdflib.namespace import SDO
    # g = Graph()
    # g.parse("/Users/csmith/Data/soso/all_edi_test_graph/combined.ttl", format="turtle")
    # lake_query = """
    # SELECT ?subject ?identifier
    # WHERE {
    #     ?subject :keywords "lakes" .
    #     ?subject :identifier ?identifier .
    # }
    # """
    # res = g.query(lake_query)
    # for row in res:
    #     print(row)

    # # Iterate through the namespace bindings
    # ns_manager = g.namespace_manager
    # for prefix, uri in ns_manager.namespaces():
    #     print(f"Prefix: {prefix}, URI: {uri}")
