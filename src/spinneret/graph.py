"""The graph module"""

from rdflib import Graph, Literal, URIRef, BNode
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
            f = Graph()
            f.parse(filename, format="json-ld")

            # TODO Follow this pattern to identify Literals for potential
            #  conversion to URIRef. Encapsulate each path in a function to
            #  be called in the parsing loop.
            for s, p, o in f.triples((None, None, None)):
                # Determine if p is schema:keywords
                if p == URIRef("https://schema.org/keywords") and isinstance(o, BNode):
                    # Get the value of the BNode
                    for s2, p2, o2 in f.triples((o, None, None)):
                        # print(s2, p2, o2)
                        if o2 == URIRef("https://schema.org/DefinedTerm"):
                            # Get the url of the DefinedTerm
                            for s3, p3, o3 in f.triples(
                                (s2, URIRef("https://schema.org/url"), None)
                            ):
                                print(s3, p3, o3)
                                # TODO convert to URIRef if is Literal and is_url

            # TODO g.add(f)  # Add the parsed graph to the combined graph

    # Load vocabularies
    if vocabulary_files is not None:
        for filename in vocabulary_files:
            g.parse(filename, format=guess_format(filename))

    return g


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
