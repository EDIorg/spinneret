"""The graph module"""

from rdflib import Graph
from rdflib.util import guess_format


def load_metadata(files: list) -> Graph:
    """
    :param files:   List of file paths to metadata in JSON-LD format
    :returns:       Graph of the combined metadata files
    """
    g = Graph()
    for filename in files:
        g.parse(filename)
    return g


def load_vocabularies(files: list) -> Graph:
    """
    :param files:   List of file paths to vocabularies
    :returns:       Graph of the combined vocabularies
    :notes: Vocabulary formats are identified by the file extension according
        to `rdflib.util.guess_format`
    """
    g = Graph()
    for filename in files:
        g.parse(filename, format=guess_format(filename))
    return g


if __name__ == "__main__":
    # Example usage
    WORKING_DIR = "/Users/csmith/Data/soso/all_edi_test_results"
    list_of_files = ["edi.1.1.json", "edi.3.10.json", "edi.5.5.json"]
    working_files = [WORKING_DIR + "/" + f for f in list_of_files]
    res = load_metadata(working_files)

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
    # g = load_metadata(working_files)

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
    #
    # # Iterate through the namespace bindings
    # ns_manager = g.namespace_manager
    # for prefix, uri in ns_manager.namespaces():
    #     print(f"Prefix: {prefix}, URI: {uri}")
    #
