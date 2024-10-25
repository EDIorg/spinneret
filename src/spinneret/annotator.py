"""The annotator module"""

import os
from json import loads, decoder
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
    wb = pd.read_csv(workbook_path, sep="\t", encoding="utf-8", dtype=str)

    # Iterate over workbook rows and annotate
    wb_additional_rows = pd.DataFrame(columns=wb.columns)
    for index, row in wb.iterrows():

        # Operate on a copy of the row to avoid warnings
        modified_row = row.copy()
        if modified_row["element"] == "dataset":
            modified_row["predicate"] = "is about"
            modified_row["predicate_id"] = "http://purl.obolibrary.org/obo/IAO_0000136"
        elif modified_row["element"] == "attribute":
            modified_row["predicate"] = "contains measurements of type"
            modified_row["predicate_id"] = (
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
            modified_row["object"] = annotation[0]["label"]
            modified_row["object_id"] = annotation[0]["uri"]
            modified_row["author"] = "BioPortal Annotator"
            modified_row["date"] = pd.Timestamp.now()
            wb.loc[index] = modified_row  # Update the row in the workbook
        if len(annotation) > 1:
            for item in annotation[1:]:
                # Create row
                new_row = row.copy()
                if new_row["element"] == "dataset":
                    new_row["predicate"] = "is about"
                    new_row["predicate_id"] = (
                        "http://purl.obolibrary.org/obo/IAO_0000136"
                    )
                elif new_row["element"] == "attribute":
                    new_row["predicate"] = "contains measurements of type"
                    new_row["predicate_id"] = (
                        "http://ecoinformatics.org/oboe/oboe.1.2/"
                        "oboe-core.owl#containsMeasurementsOfType"
                    )
                new_row["object"] = item["label"]
                new_row["object_id"] = item["uri"]
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


def get_qudt_annotation(text: str) -> Union[list, None]:
    """Get an annotation from the QUDT API

    :param text: The text to be annotated. This should be the value from the
        EML `standardUnit` or `customUnit` element.
    :returns: A list of dictionaries, each with the annotation keys `label`
        and `uri`, corresponding to the preferred label and URI of the
        annotated concept. None if the request fails.

    :notes: This function queries the Unit Annotations Service
        https://vocab.lternet.edu/unitsws.html, developed by the EDI and LTER
        units working group, for a match of the input `text` to a QUDT unit via
        the service mapping.
    """
    url = (
        f"https://vocab.lternet.edu/webservice/unitsws.php?rawunit={text}&"
        f"returntype=json"
    )
    try:
        r = get(url, timeout=10)
        r.raise_for_status()
    except exceptions.RequestException as e:
        print(f"Error calling {url}: {e}")
        return None
    if r.text == "No_Match":
        return None
    try:  # the service has a few JSON encoding bugs
        json = loads(r.text)
    except decoder.JSONDecodeError as e:
        print(f"Error decoding JSON from {url}: {e}")
        return None
    label = json["qudtLabel"]
    uri = json["qudtURI"]
    return [{"label": label, "uri": uri}]


def add_qudt_annotations_to_workbook(
    workbook: Union[str, pd.core.frame.DataFrame],
    eml: Union[str, etree._ElementTree],
    output_path: str = None,
    overwrite: bool = False,
) -> pd.core.frame.DataFrame:
    """
    :param workbook: Either the path to the workbook to be annotated, or the
        workbook itself as a pandas DataFrame.
    :param eml: Either the path to the EML file corresponding to the workbook,
        or the EML file itself as an lxml etree.
    :param output_path: The path to write the annotated workbook.
    :param overwrite: If True, overwrite existing QUDT annotations in the
        workbook. This enables updating the annotations in the workbook with
        the latest QUDT annotations.
    :returns: Workbook with QUDT annotations."""

    # Load the workbook and EML for processing
    if isinstance(workbook, str):
        wb = pd.read_csv(workbook, sep="\t", encoding="utf-8", dtype=str)
    else:
        wb = workbook
    wb = wb.astype(str)  # dtype=str (above) not working for empty columns
    if isinstance(eml, str):
        eml = etree.parse(eml, parser=etree.XMLParser(remove_blank_text=True))

    # Remove existing QUDT annotations if overwrite is True
    if overwrite:
        wb = wb[~wb["object_id"].str.contains("http://qudt.org/vocab/unit/")]

    # Iterate over EML units and add QUDT annotations to the workbook
    units = eml.xpath("//standardUnit") + eml.xpath("//customUnit")
    for unit in units:
        attribute_element = unit.xpath("ancestor::attribute[1]")
        attribute_xpath = eml.getpath(attribute_element[0])

        # Skip if a QUDT annotation already exists for the attribute xpath and
        # overwrite is False
        rows = wb[wb["element_xpath"] == attribute_xpath].index
        base_uri = "http://qudt.org/vocab/unit/"
        has_qudt_annotation = wb.loc[rows, "object_id"].str.contains(base_uri)
        if has_qudt_annotation.any() and not overwrite:
            continue

        # Otherwise add the QUDT annotation
        annotation = get_qudt_annotation(unit.text)
        if annotation is not None:
            modified_row = wb.loc[rows[0]].copy()  # copy avoids warnings
            modified_row["predicate"] = "uses standard"
            modified_row["predicate_id"] = (
                "http://ecoinformatics.org/oboe/oboe.1.2/oboe-core.owl#usesStandard"
            )
            modified_row["object"] = annotation[0]["label"]
            modified_row["object_id"] = annotation[0]["uri"]
            modified_row["author"] = "Unit Webservice Service"
            modified_row["date"] = pd.Timestamp.now()
            wb.loc[len(wb)] = modified_row

    if output_path:
        wb.to_csv(output_path, sep="\t", index=False, encoding="utf-8")
    return wb
