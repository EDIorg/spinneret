"""The annotator module"""

import os
from typing import Union
from requests import get, exceptions
import pandas as pd
from lxml import etree


# pylint: disable=too-many-locals
def get_bioportal_annotation(
    text: str,
    api_key: str,
    ontologies: str,
    semantic_types: str = "",
    expand_semantic_types_hierarchy: str = "false",
    expand_class_hierarchy: str = "false",
    class_hierarchy_max_level: int = 0,
    expand_mappings: str = "false",
    stop_words: str = "",
    minimum_match_length: int = 3,
    exclude_numbers: str = "false",
    whole_word_only: str = "true",
    exclude_synonyms: str = "false",
    longest_only: str = "false",
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


def annotate_eml(eml_path: str, workbook_path: str, output_path: str) -> None:
    """Annotate an EML file with terms from the corresponding workbook

    :param eml_path: The path to the EML file to be annotated.
    :param workbook_path: The path to the workbook corresponding to the EML file.
    :param output_path: The path to write the annotated EML file.
    :returns: None

    :notes: The EML file is annotated with terms from the corresponding workbook.
        Terms from the workbook are added even if they are already present in
        the EML file.
    """
    # Load the EML and workbook for processing
    eml = etree.parse(eml_path, parser=etree.XMLParser(remove_blank_text=True))
    wb = pd.read_csv(workbook_path, sep="\t", encoding="utf-8")

    # Iterate over workbook rows and annotate the EML
    for _, row in wb.iterrows():

        # Only annotate if required components are present
        if (
            not pd.isnull(row["predicate"])
            and not pd.isnull(row["predicate_id"])
            and not pd.isnull(row["object"])
            and not pd.isnull(row["object_id"])
        ):
            # Create the annotation element
            annotation = create_annotation_element(
                predicate_label=row["predicate"],
                predicate_id=row["predicate_id"],
                object_label=row["object"],
                object_id=row["object_id"],
            )

            # Insert the annotation
            if row["element"] == "dataset":

                # Insert the annotation before the required contact element,
                # and any optional elements preceding the contact element, to
                # correctly locate dataset level annotations according to the
                # EML schema.
                root = eml.getroot()
                dataset = root.find(".//dataset")
                if dataset.find("purpose"):
                    reference_element = dataset.find("purpose")
                elif dataset.find("introduction"):
                    reference_element = dataset.find("introduction")
                elif dataset.find("gettingStarted"):
                    reference_element = dataset.find("gettingStarted")
                elif dataset.find("acknowledgements"):
                    reference_element = dataset.find("acknowledgements")
                elif dataset.find("maintenance"):
                    reference_element = dataset.find("maintenance")
                else:
                    reference_element = dataset.find("contact")
                dataset.insert(dataset.index(reference_element), annotation)

            elif row["element"] == "attribute":

                # Convert absolute XPath to relative path to avoid errors
                attribute_xpath = row["element_xpath"].replace("/eml:eml", "./")

                # Insert the annotation at the end of the attribute list.
                root = eml.getroot()
                attribute = root.find(attribute_xpath)
                attribute.insert(len(attribute) + 1, annotation)

    # Write eml to file
    eml.write(output_path, pretty_print=True, encoding="utf-8", xml_declaration=True)


def create_annotation_element(predicate_label, predicate_id, object_label, object_id):
    """Create an EML annotation element

    :param predicate_label: The predicate label of the annotation.
    :param predicate_id: The URI of the predicate.
    :param object_label: The object label of the annotation.
    :param object_id: The URI of the object.
    """
    annotation_elem = etree.Element("annotation")

    property_uri_elem = etree.SubElement(annotation_elem, "propertyURI")
    property_uri_elem.attrib["label"] = predicate_label
    property_uri_elem.text = predicate_id

    value_uri_elem = etree.SubElement(annotation_elem, "valueURI")
    value_uri_elem.attrib["label"] = object_label
    value_uri_elem.text = object_id

    return annotation_elem
