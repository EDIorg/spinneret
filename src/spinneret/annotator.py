"""The annotator module"""

import os
from typing import Union
from requests import get, exceptions
import pandas as pd


# pylint: disable=too-many-locals
def get_bioportal_annotation(
    text: str,
    api_key: str,
    ontologies: str,
    semantic_types: str = "",
    expand_semantic_types_hierarchy: bool = False,
    expand_class_hierarchy: bool = False,
    class_hierarchy_max_level: int = 0,
    expand_mappings: bool = False,
    stop_words: str = "",
    minimum_match_length: int = 3,
    exclude_numbers: bool = False,
    whole_word_only: bool = True,
    exclude_synonyms: bool = False,
    longest_only: bool = False,
) -> Union[list, None]:
    """Get an annotation from the BioPortal API

    :param text: The text to be annotated.
    :param api_key: The BioPortal API key.
    :param ontologies: The ontologies to use for annotation.
    :param semantic_types: The semantic types to use for annotation.
    :param expand_semantic_types_hierarchy: true means to use the semantic
        types passed in the "semantic_types" parameter as well as all their
        immediate children. false means to use ONLY the semantic types passed
        in the "semantic_types" parameter.
    :param expand_class_hierarchy:  used only in conjunction with
        "class_hierarchy_max_level" parameter; determines whether or not to
        include ancestors of the given class when performing an annotation.
    :param class_hierarchy_max_level: the depth of the hierarchy to use when
        performing an annotation.
    :param expand_mappings: true means that the following manual mappings will
        be used in annotation: UMLS, REST, CUI, OBOXREF.
    :param stop_words: a comma-separated list of words to ignore in the text.
    :param minimum_match_length: the minimum number of characters in a term
        that must be matched in the text.
    :param exclude_numbers: true means to exclude numbers from annotation.
    :param whole_word_only: true means to match whole words only.
    :param exclude_synonyms: true means to exclude synonyms from annotation.
    :param longest_only: true means that only the longest match for a given
        phrase will be returned.

    :returns: A list of dictionaries, each with the annotation keys `label`
        and `uri`, corresponding to the preferred label and URI of the
        annotated concept. None if the request fails.

    :notes: This function is a wrapper for the BioPortal API. The BioPortal API
        is a repository of biomedical ontologies with a RESTful API that allows
        users to annotate text with ontology concepts. The API is documented at
        https://data.bioontology.org/documentation#nav_annotator.

        This function requires an API key from BioPortal. To obtain an API key,
        users must register at https://bioportal.bioontology.org/account. The
        key can be loaded as an environment variable from the configuration
        file (see `utilities.load_configuration`).
    """
    # Construct the query
    url = "https://data.bioontology.org/annotator"
    payload = {
        "text": text,
        "apikey": api_key,
        "ontologies": ontologies,
        "semantic_types": semantic_types,
        "expand_semantic_types_hierarchy": expand_semantic_types_hierarchy,
        "expand_class_hierarchy": expand_class_hierarchy,
        "class_hierarchy_max_level": class_hierarchy_max_level,
        "expand_mappings": expand_mappings,
        "stop_words": stop_words,
        "minimum_match_length": minimum_match_length,
        "exclude_numbers": exclude_numbers,
        "whole_word_only": whole_word_only,
        "exclude_synonyms": exclude_synonyms,
        "longest_only": longest_only,
        "page_size": 100,  # to circumvent pagination
        "format": "json",  # being explicit here, even though it's the default
    }
    # Get annotations
    try:
        r = get(url, params=payload, timeout=10)
        r.raise_for_status()
    except exceptions.RequestException as e:
        print(f"Error calling https://data.bioontology.org/annotator: {e}")
        return None

    # Parse the results
    annotations = []
    for item in r.json():
        self_link = item.get("annotatedClass", {}).get("links").get("self", None)
        try:
            r = get(self_link, params={"apikey": api_key}, timeout=10)
            r.raise_for_status()
        except exceptions.RequestException as e:
            print(f"Error calling {self_link}: {e}")
            return None
        uri = r.json().get("@id", None)
        label = r.json().get("prefLabel", None)
        annotations.append({"label": label, "uri": uri})
    return annotations


def annotate_workbook(workbook_path: str, output_path: str) -> None:
    """Annotate a workbook with automated annotation

    :param workbook_path: The path to the workbook to be annotated
        corresponding to the EML file.
    :param output_path: The path to write the annotated workbook.
    :returns: None
    :notes: The workbook is annotated by annotators best suited for the XPaths
        in the EML file. The annotated workbook is written back to the same
        path as the original workbook.
    """
    # Ensure the workbook and eml file match to avoid errors
    print(f"Annotating workbook {workbook_path}")

    # Load the workbook and EML for processing
    wb = pd.read_csv(workbook_path, sep="\t", encoding="utf-8")

    # Iterate over workbook rows and annotate
    wb_additional_rows = pd.DataFrame(columns=wb.columns)
    for index, row in wb.iterrows():

        # Adding standard predicates based on the subject element name
        if row["element"] == "dataset":
            wb.loc[index, "predicate"] = "is about"
            wb.loc[index, "predicate_id"] = "http://purl.obolibrary.org/obo/IAO_0000136"
        elif row["element"] == "attribute":
            wb.loc[index, "predicate"] = "contains measurements of type"
            wb.loc[index, "predicate_id"] = (
                "http://ecoinformatics.org/oboe/oboe.1.2/oboe-core.owl#containsMeasurementsOfType"
            )

        # Get annotations for the element's descriptive text
        if row["element"] == "dataset":
            annotation = get_bioportal_annotation(
                text=row["description"],
                api_key=os.environ["BIOPORTAL_API_KEY"],
                ontologies="ENVO",  # ENVO provides environmental terms
                exclude_synonyms="true",
            )
        elif row["element"] == "attribute":
            annotation = get_bioportal_annotation(
                text=row["description"],
                api_key=os.environ["BIOPORTAL_API_KEY"],
                ontologies="ECSO",  # ECSO provides measurment terms
                exclude_synonyms="true",
            )
        else:
            continue

        # Add annotations to the workbook. Add first annotation to row then the
        # remainder to a separate data frame to be appended at the end.
        if annotation:
            wb.loc[index, "object"] = annotation[0]["label"]
            wb.loc[index, "object_id"] = annotation[0]["uri"]
            wb.loc[index, "author"] = "BioPortal Annotator"
            wb.loc[index, "date"] = pd.Timestamp.now()
        if len(annotation) > 1:
            for item in annotation[1:]:
                # Create row
                new_row = wb.loc[index]
                new_row.loc["object"] = item["label"]
                new_row.loc["object_id"] = item["uri"]
                new_row["author"] = "BioPortal Annotator"
                new_row["date"] = pd.Timestamp.now()
                # Append row to additional rows df
                wb_additional_rows.loc[len(wb_additional_rows)] = new_row

    # Append additional rows to the workbook
    wb = pd.concat([wb, wb_additional_rows], ignore_index=True)

    # Write the annotated workbook back to the original path
    wb.to_csv(output_path, sep="\t", index=False, encoding="utf-8")
