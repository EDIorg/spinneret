"""The graph module"""

from rdflib import Graph


def combine_jsonld_files(files: list) -> Graph:
    """
    :param files:   List of file paths to JSON-LD files
    :returns:       Graph of the combined JSON-LD files
    """
    g = Graph()
    for filename in files:
        g.parse(filename)
    return g


if __name__ == "__main__":
    # Example usage
    WORKING_DIR = "/Users/csmith/Data/soso/all_edi_test_results"
    list_of_files = ["edi.1.1.json", "edi.3.10.json", "edi.5.5.json"]
    working_files = [WORKING_DIR + "/" + f for f in list_of_files]
    res = combine_jsonld_files(working_files)

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
    # g = combine_jsonld_files(working_files)

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
