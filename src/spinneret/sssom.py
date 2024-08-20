"""The SSSOM module"""

import pandas as pd
from rdflib import Graph


def from_lter(path_in: str, path_out: str) -> dict:
    """Create SSSOM for the LTER Controlled Vocabulary

    Create SSSOM files (Simple Standard for Sharing Ontological Mappings) for
    aligning the LTER Controlled Vocabulary with other vocabularies and
    ontologies. The returned SSSOM files embody a 3/5 star rating based on
    https://mapping-commons.github.io/sssom/spec/#minimum. See the related
    Python toolkit to parse, convert, etc. the SSSOM:
    https://mapping-commons.github.io/sssom-py/index.html#. For definitions
    of fields returned in the SSSOM files see:
    https://mapping-commons.github.io/sssom/.

    :param path_in: Absolute path to LTER CV .rdf file
    :param path_out:    Absolute path to directory where SSSOM files will be written
    :returns:   Dictionary with keys 'data_path' and 'meta_path' and values as
                the absolute paths to the SSSOM data and metadata files

    :notes: Overwriting of the SSSOM does not occur with subsequent calls of this
            function.
    """
    data_path = path_out + "/" + "lter.sssom.tsv"
    meta_path = path_out + "/" + "lter.sssom.yml"
    g = Graph()
    g.parse(path_in)
    data = []
    for s, p, o in g:
        if str(p) == "http://www.w3.org/2004/02/skos/core#prefLabel":
            row = [str(s), str(o)]
            row.extend([""] * 10)
            data.append(row)
    cols = [
        "subject_id",
        "subject_label",
        "predicate_id",
        "object_id",
        "object_label",
        "confidence",
        "comment",
        "mapping_justification",
        "mapping_date",
        "author_id",
        "subject_source_version",
        "object_source_version",
    ]
    data = pd.DataFrame(data, columns=cols)
    data.to_csv(data_path, sep="\t", index=False, mode="x")
    meta = [
        "mapping_set_id:",
        "license:",
        "mapping_set_version:",
        "mapping_set_description:",
        "object_source:",
        "subject_source:",
        "curie_map:",
    ]
    meta = "\n".join(meta)
    with open(meta_path, mode="w+", encoding="utf-8") as f:
        f.write(meta)
    res = {"data_path": data_path, "meta_path": meta_path}
    return res
