"""The annotator module"""

import os
import tempfile
from importlib import resources
from json import loads, decoder, load
from typing import Union
from requests import get, exceptions
import pandas as pd
from lxml import etree
from spinneret.workbook import (
    delete_annotations,
    initialize_workbook_row,
    get_package_id,
    get_package_url,
    get_subject_and_context,
    get_description,
    delete_duplicate_annotations,
)
from spinneret.utilities import (
    load_eml,
    load_workbook,
    write_workbook,
    write_eml,
    expand_curie,
)

# pylint: disable=too-many-lines


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


def annotate_workbook(
    workbook_path: str,
    eml_path: str,
    output_path: str,
    annotator: str,
    local_model: str = None,
    return_ungrounded: bool = False,
) -> None:
    """Annotate a workbook with automated annotation

    :param workbook_path: The path to the workbook to be annotated
        corresponding to the EML file.
    :param eml_path: The path to the EML file corresponding to the workbook.
    :param output_path: The path to write the annotated workbook.
    :param annotator: The annotator to use for grounding. Options are "ontogpt"
        and "bioportal". OntoGPT requires setup and configuration described in
        the `get_ontogpt_annotation` function. Similarly, BioPortal requires
        an API key and is described in the `get_bioportal_annotation` function.
    :param local_model: See `get_ontogpt_annotation` documentation for details.
    :param return_ungrounded: See `get_ontogpt_annotation` documentation for
        details.
    :returns: None
    :notes: The workbook is annotated by annotators best suited for the XPaths
        in the EML file. The annotated workbook is written back to the same
        path as the original workbook.
    """
    print(f"Annotating workbook {workbook_path}")

    # Ensure the workbook and eml file match to avoid errors
    pid = os.path.basename(workbook_path).split("_")[0]
    eml_file = pid + ".xml"
    if eml_file not in eml_path:
        print(f"EML file {eml_file} does not match workbook {workbook_path}")
        return None

    # Load the workbook and EML for processing
    wb = load_workbook(workbook_path)
    eml = load_eml(eml_path)

    # Run workbook annotators, results of one are used as input for the next
    if annotator == "bioportal":
        wb = add_dataset_annotations_to_workbook(wb, eml)
        wb = add_measurement_type_annotations_to_workbook(wb, eml, annotator=annotator)
    elif annotator == "ontogpt":
        wb = add_env_broad_scale_annotations_to_workbook(
            wb, eml, local_model=local_model, return_ungrounded=return_ungrounded
        )
        wb = add_env_local_scale_annotations_to_workbook(
            wb, eml, local_model=local_model, return_ungrounded=return_ungrounded
        )
        wb = add_process_annotations_to_workbook(
            wb, eml, local_model=local_model, return_ungrounded=return_ungrounded
        )
        wb = add_methods_annotations_to_workbook(
            wb, eml, local_model=local_model, return_ungrounded=return_ungrounded
        )
        wb = add_research_topic_annotations_to_workbook(
            wb, eml, local_model=local_model, return_ungrounded=return_ungrounded
        )
        wb = add_measurement_type_annotations_to_workbook(
            wb,
            eml,
            annotator="ontogpt",
            local_model=local_model,
            return_ungrounded=return_ungrounded,
        )
        wb = add_env_medium_annotations_to_workbook(
            wb, eml, local_model=local_model, return_ungrounded=return_ungrounded
        )
    wb = add_qudt_annotations_to_workbook(wb, eml)  # irrespective of annotator

    write_workbook(wb, output_path)
    return None


def annotate_eml(
    eml: Union[str, etree._ElementTree],
    workbook: Union[str, pd.core.frame.DataFrame],
    output_path: str = None,
) -> etree._ElementTree:
    """Annotate an EML file with terms from the corresponding workbook

    :param eml: Either the path to the EML file corresponding to the
        `workbook`, or the EML file itself as an lxml etree.
    :param workbook: Either the path to the workbook corresponding to the
        `eml`, or the workbook itself as a pandas DataFrame.
    :param output_path: The path to write the annotated EML file.
    :returns: The annotated EML file as an lxml etree.

    :notes: The EML file is annotated with terms from the corresponding
        workbook. Terms from the workbook are added even if they are already
        present in the EML file.
    """
    # Load the EML and workbook for processing
    eml = load_eml(eml)
    wb = load_workbook(workbook)

    # Iterate over workbook rows and annotate the EML
    for _, row in wb.iterrows():

        # Only annotate if required components are present
        if (
            not pd.isnull(row["predicate"])
            and not pd.isnull(row["predicate_id"])
            and not pd.isnull(row["object"])
            and not pd.isnull(row["object_id"])
        ):
            # Skip if the object_id is an ungrounded concept from OntoGPT.
            # These are not valid annotations.
            if row["object_id"].startswith("AUTO:"):
                continue

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

    if output_path:
        write_eml(eml, output_path)
    return eml


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
    :param overwrite: If True, overwrite existing `QUDT` annotations in the
        `workbook, so a fresh set may be created.
    :returns: Workbook with QUDT annotations."""

    # Parameters for the function
    predicate = "uses standard"

    # Load the workbook and EML for processing
    wb = load_workbook(workbook)
    eml = load_eml(eml)

    # Remove existing QUDT annotations if overwrite is True, using a set of
    # criteria that accurately define the annotations to remove.
    if overwrite:
        wb = delete_annotations(
            workbook=wb,
            criteria={
                "element": "attribute",
                "object_id": "http://qudt.org/vocab/unit/",
                "author": "spinneret.annotator.get_qudt_annotation",
            },
        )

    # Iterate over EML units and add QUDT annotations to the workbook
    units = eml.xpath("//standardUnit") + eml.xpath("//customUnit")
    for unit in units:
        attribute_element = unit.xpath("ancestor::attribute[1]")[0]
        attribute_xpath = eml.getpath(attribute_element)
        attribute_description = get_description(attribute_element)

        # Skip if this element already has an annotation in the workbook, to
        # prevent duplicate annotations from being added.
        if has_annotation(wb, attribute_xpath, predicate):
            return wb

        # Reuse existing annotations for elements with identical tag names,
        # descriptions, and predicate labels, to reduce redundant processing.
        # Note this assumes semantic equivalence between elements with matching
        # tags and descriptions.
        annotations = get_annotation_from_workbook(
            workbook=wb,
            element=attribute_element.tag,
            description=attribute_description,
            predicate=predicate,
        )

        if annotations is None:
            # Get the QUDT annotation
            annotations = get_qudt_annotation(unit.text)

        if annotations is not None:
            for annotation in annotations:
                row = initialize_workbook_row()
                row["package_id"] = get_package_id(eml)
                row["url"] = get_package_url(eml)
                row["element"] = attribute_element.tag
                if "id" in attribute_element.attrib:
                    row["element_id"] = attribute_element.attrib["id"]
                else:
                    row["element_id"] = pd.NA
                row["element_xpath"] = attribute_xpath
                row["context"] = get_subject_and_context(attribute_element)["context"]
                row["description"] = attribute_description
                row["subject"] = get_subject_and_context(attribute_element)["subject"]
                row["predicate"] = predicate
                row["predicate_id"] = (
                    "http://ecoinformatics.org/oboe/oboe.1.2/oboe-core.owl#usesStandard"
                )
                row["object"] = annotation["label"]
                row["object_id"] = annotation["uri"]
                row["author"] = "spinneret.annotator.get_qudt_annotation"
                row["date"] = pd.Timestamp.now()
                row = pd.DataFrame([row], dtype=str)
                wb = pd.concat([wb, row], ignore_index=True)
            wb = delete_duplicate_annotations(wb)

    if output_path:
        write_workbook(wb, output_path)
    return wb


def add_dataset_annotations_to_workbook(
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
    :param overwrite: If True, overwrite existing `dataset` annotations in the
        workbook, so a fresh set may be created.
    :returns: Workbook with dataset annotations."""

    # Load the workbook and EML for processing
    wb = load_workbook(workbook)
    eml = load_eml(eml)

    # Set the author identifier for consistent reference below
    author = "spinneret.annotator.get_bioportal_annotation"

    # Remove existing dataset annotations if overwrite is True, using a set of
    # criteria that accurately define the annotations to remove.
    if overwrite:
        wb = delete_annotations(
            workbook=wb,
            criteria={
                "element": "dataset",
                "element_xpath": "/eml:eml/dataset",
                "author": author,
            },
        )

    # Get the dataset annotations
    dataset_element = eml.xpath("//dataset")[0]
    element_description = get_description(dataset_element)
    annotations = get_bioportal_annotation(  # expecting a list of annotations
        text=element_description,
        api_key=os.environ["BIOPORTAL_API_KEY"],
        ontologies="ENVO",  # ENVO provides environmental terms
        exclude_synonyms="true",
    )

    # Add dataset annotations to the workbook
    if annotations is not None:
        for annotation in annotations:
            row = initialize_workbook_row()
            row["package_id"] = get_package_id(eml)
            row["url"] = get_package_url(eml)
            row["element"] = dataset_element.tag
            if "id" in dataset_element.attrib:
                row["element_id"] = dataset_element.attrib["id"]
            else:
                row["element_id"] = pd.NA
            row["element_xpath"] = eml.getpath(dataset_element)
            row["context"] = get_subject_and_context(dataset_element)["context"]
            row["description"] = element_description
            row["subject"] = get_subject_and_context(dataset_element)["subject"]
            row["predicate"] = "is about"
            row["predicate_id"] = "http://purl.obolibrary.org/obo/IAO_0000136"
            row["object"] = annotation["label"]
            row["object_id"] = annotation["uri"]
            row["author"] = author
            row["date"] = pd.Timestamp.now()
            row = pd.DataFrame([row], dtype=str)
            wb = pd.concat([wb, row], ignore_index=True)
        wb = delete_duplicate_annotations(wb)

    if output_path:
        write_workbook(wb, output_path)
    return wb


# pylint: disable=too-many-branches
def add_measurement_type_annotations_to_workbook(
    workbook: Union[str, pd.core.frame.DataFrame],
    eml: Union[str, etree._ElementTree],
    annotator: str,
    output_path: str = None,
    overwrite: bool = False,
    local_model: str = None,
    return_ungrounded: bool = False,
) -> pd.core.frame.DataFrame:
    """
    :param workbook: Either the path to the workbook to be annotated, or the
        workbook itself as a pandas DataFrame.
    :param eml: Either the path to the EML file corresponding to the workbook,
        or the EML file itself as an lxml etree.
    :param annotator: The annotator to use for grounding. Options are "ontogpt"
        and "bioportal". OntoGPT requires setup and configuration described in
        the `get_ontogpt_annotation` function. Similarly, BioPortal requires
        an API key and is described in the `get_bioportal_annotation` function.
    :param output_path: The path to write the annotated workbook.
    :param overwrite: If True, overwrite existing `measurement type`
        annotations in the workbook, so a fresh set may be created.
    :param local_model: Required if `annotator` is "ontogpt". See
        `get_ontogpt_annotation` documentation for details.
    :param return_ungrounded: An option if `annotator` is "ontogpt". See
        `get_ontogpt_annotation` documentation for details.
    :returns: Workbook with measurement type annotations."""

    # Parameters for the function
    predicate = "contains measurements of type"

    # Load the workbook and EML for processing
    wb = load_workbook(workbook)
    eml = load_eml(eml)

    # Remove existing measurement type annotations if overwrite is True, using
    # a set of criteria that accurately define the annotations to remove.
    if overwrite:
        wb = delete_annotations(
            workbook=wb,
            criteria={
                "element": "attribute",
                "element_xpath": "/attribute",
                "author": "spinneret.annotator",  # any spinneret annotator
            },
        )

    # Iterate over EML attributes and add measurement type annotations to the
    # workbook
    attributes = eml.xpath("//attribute")
    for attribute in attributes:
        attribute_element = attribute
        attribute_xpath = eml.getpath(attribute_element)
        attribute_description = get_description(attribute_element)

        # Skip if this element already has an annotation in the workbook, to
        # prevent duplicate annotations from being added.
        if has_annotation(wb, attribute_xpath, predicate):
            return wb

        # Reuse existing annotations for elements with identical tag names,
        # descriptions, and predicate labels, to reduce redundant processing.
        # Note this assumes semantic equivalence between elements with matching
        # tags and descriptions.
        annotations = get_annotation_from_workbook(
            workbook=wb,
            element=attribute_element.tag,
            description=attribute_description,
            predicate=predicate,
        )

        if annotations is None:
            # Select an annotator, and get the measurement type annotations
            if annotator.lower() == "ontogpt":
                annotations = get_ontogpt_annotation(
                    text=attribute_description,
                    template="contains_measurement_of_type",
                    local_model=local_model,
                    return_ungrounded=return_ungrounded,
                )
            else:
                annotations = (
                    get_bioportal_annotation(  # expecting a list of annotations
                        text=attribute_description,
                        api_key=os.environ["BIOPORTAL_API_KEY"],
                        ontologies="ECSO",  # ECSO provides measurment terms
                        exclude_synonyms="true",
                    )
                )

        # Add the measurement type annotations to the workbook
        if annotations is not None:
            for annotation in annotations:
                row = initialize_workbook_row()
                row["package_id"] = get_package_id(eml)
                row["url"] = get_package_url(eml)
                row["element"] = attribute_element.tag
                if "id" in attribute_element.attrib:
                    row["element_id"] = attribute_element.attrib["id"]
                else:
                    row["element_id"] = pd.NA
                row["element_xpath"] = attribute_xpath
                row["context"] = get_subject_and_context(attribute_element)["context"]
                row["description"] = get_description(attribute_element)
                row["subject"] = get_subject_and_context(attribute_element)["subject"]
                row["predicate"] = predicate
                row["predicate_id"] = (
                    "http://ecoinformatics.org/oboe/oboe.1.2/oboe-core.owl#"
                    "containsMeasurementsOfType"
                )
                row["object"] = annotation["label"]
                row["object_id"] = annotation["uri"]
                if annotator.lower() == "ontogpt":
                    row["author"] = "spinneret.annotator.get_ontogpt_annotation"
                elif annotator.lower() == "bioportal":
                    row["author"] = "spinneret.annotator.get_bioportal_annotation"
                row["date"] = pd.Timestamp.now()
                row = pd.DataFrame([row], dtype=str)
                wb = pd.concat([wb, row], ignore_index=True)
            wb = delete_duplicate_annotations(wb)

    if output_path:
        write_workbook(wb, output_path)
    return wb


def get_ontogpt_annotation(
    text: str, template: str, local_model: str = None, return_ungrounded: bool = False
) -> Union[list, None]:
    """
    :param text: The text to be annotated.
    :param template: Name of OntoGPT template to use for grounding. Available
        templates are in src/data/ontogpt/templates. Omit the file extension.
    :param local_model: The local language model to use (e.g. `llama3.2`). This
        should be one of the options available from `ollama` (see
        https://ollama.com/library) and should be installed locally. If `None`,
        the configured remote model will be used. See the OntoGPT documentation
        for more information.
    :param return_ungrounded: If True, return ungrounded annotations. These
        may be useful in identifying potential concepts to add to a vocabulary,
        or to identify concepts that a human curator may be capable of
        grounding.
    :returns: A list of dictionaries, each with the annotation keys `label`
        and `uri`. None if the request fails or no annotations are found.
    :notes: This function is a wrapper for the OntoGPT API. Set up of OntoGPT
        is required to use this function. For more information, see:
        https://monarch-initiative.github.io/ontogpt/.
    """
    # OntoGPT transacts in files, so we write the input text to a temporary
    # file and receive the results as a JSON file. Once the results are parsed
    # we can discard the files.
    with tempfile.TemporaryDirectory() as temp_dir:
        input_file = os.path.join(temp_dir, "input.txt")
        with open(input_file, "w", encoding="utf-8") as f:
            f.write(text)
        template_file = resources.files("spinneret.data.ontogpt.templates").joinpath(
            f"{template}.yaml"
        )
        output_file = os.path.join(temp_dir, "output.json")

        # Call OntoGPT
        cmd = (
            f"ontogpt extract -i {input_file} -t {template_file} "
            f"--output-format json -o {output_file}"
        )
        if local_model is not None:
            cmd += f"  -m ollama/{local_model}"
        try:
            os.system(cmd)
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"Error calling OntoGPT: {e}")
            return None

        # Parse the results
        try:  # Occasionally, no file is returned. This is a bug in OntoGPT.
            with open(output_file, "r", encoding="utf-8") as f:
                r = load(f)
        except FileNotFoundError as e:
            print(f"Error reading OntoGPT output file: {e}")
            return None
        named_entities = r.get("named_entities")
        if named_entities is None:  # OntoGPT couldn't find any annotations
            return None
        annotations = []
        for item in named_entities:
            uri = item.get("id")
            label = item.get("label")
            ungrounded = uri.startswith("AUTO:")
            if ungrounded and not return_ungrounded:
                continue
            uri = expand_curie(uri)
            annotations.append({"label": label, "uri": uri})

    return annotations


def add_process_annotations_to_workbook(
    workbook: Union[str, pd.core.frame.DataFrame],
    eml: Union[str, etree._ElementTree],
    output_path: str = None,
    overwrite: bool = False,
    local_model: str = None,
    return_ungrounded: bool = False,
) -> pd.core.frame.DataFrame:
    """
    :param workbook: Either the path to the workbook to be annotated, or the
        workbook itself as a pandas DataFrame.
    :param eml: Either the path to the EML file corresponding to the workbook,
        or the EML file itself as an lxml etree.
    :param output_path: The path to write the annotated workbook.
    :param overwrite: If True, overwrite existing `process` annotations in the
        workbook, so a fresh set may be created.
    :param local_model: See `get_ontogpt_annotation` documentation for details.
    :param return_ungrounded: See `get_ontogpt_annotation` documentation for
        details.
    :returns: Workbook with process annotations.
    :notes: This function retrieves process annotations using OntoGPT, which
        requires setup and configuration described in the
        `get_ontogpt_annotation` function.
    """

    # Load the workbook and EML for processing
    wb = load_workbook(workbook)
    eml = load_eml(eml)

    # Parameters for the function
    dataset_element = eml.xpath("//dataset")[0]
    element_description = get_description(dataset_element)
    element_xpath = eml.getpath(dataset_element)
    predicate = "contains process"

    # Set the author identifier for consistent reference below
    author = "spinneret.annotator.get_onto_gpt_annotation"

    # Remove existing process annotations if overwrite is True, using a set of
    # criteria that accurately define the annotations to remove.
    if overwrite:
        wb = delete_annotations(
            workbook=wb,
            criteria={
                "element": "dataset",
                "element_xpath": "/eml:eml/dataset",
                "predicate": predicate,
                "author": author,
            },
        )

    # Skip if this element already has an annotation in the workbook, to
    # prevent duplicate annotations from being added.
    if has_annotation(wb, element_xpath, predicate):
        return wb

    # Reuse existing annotations for elements with identical tag names,
    # descriptions, and predicate labels, to reduce redundant processing.
    # Note this assumes semantic equivalence between elements with matching
    # tags and descriptions.
    annotations = get_annotation_from_workbook(
        workbook=wb,
        element=dataset_element.tag,
        description=element_description,
        predicate=predicate,
    )

    if annotations is None:
        # Get the process annotations
        annotations = get_ontogpt_annotation(
            text=element_description,
            template="contains_process",
            local_model=local_model,
            return_ungrounded=return_ungrounded,
        )

    # Add process annotations to the workbook
    if annotations is not None:
        for annotation in annotations:
            row = initialize_workbook_row()
            row["package_id"] = get_package_id(eml)
            row["url"] = get_package_url(eml)
            row["element"] = dataset_element.tag
            if "id" in dataset_element.attrib:
                row["element_id"] = dataset_element.attrib["id"]
            else:
                row["element_id"] = pd.NA
            row["element_xpath"] = eml.getpath(dataset_element)
            row["context"] = get_subject_and_context(dataset_element)["context"]
            row["description"] = element_description
            row["subject"] = get_subject_and_context(dataset_element)["subject"]
            row["predicate"] = predicate
            row["predicate_id"] = "http://purl.obolibrary.org/obo/BFO_0000067"
            row["object"] = annotation["label"]
            row["object_id"] = annotation["uri"]
            row["author"] = author
            row["date"] = pd.Timestamp.now()
            row = pd.DataFrame([row], dtype=str)
            wb = pd.concat([wb, row], ignore_index=True)
        wb = delete_duplicate_annotations(wb)

    if output_path:
        write_workbook(wb, output_path)
    return wb


def add_env_broad_scale_annotations_to_workbook(
    workbook: Union[str, pd.core.frame.DataFrame],
    eml: Union[str, etree._ElementTree],
    output_path: str = None,
    overwrite: bool = False,
    local_model: str = None,
    return_ungrounded: bool = False,
) -> pd.core.frame.DataFrame:
    """
    :param workbook: Either the path to the workbook to be annotated, or the
        workbook itself as a pandas DataFrame.
    :param eml: Either the path to the EML file corresponding to the workbook,
        or the EML file itself as an lxml etree.
    :param output_path: The path to write the annotated workbook.
    :param overwrite: If True, overwrite existing `broad scale environmental
        context` annotations in the workbook, so a fresh set may be created.
    :param local_model: See `get_ontogpt_annotation` documentation for details.
    :param return_ungrounded: See `get_ontogpt_annotation` documentation for
        details.
    :returns: Workbook with broad scale environmental context annotations.
    :notes: This function retrieves broad scale environmental context
        annotations using OntoGPT, which requires setup and configuration
        described in the `get_ontogpt_annotation` function.
    """

    # Load the workbook and EML for processing
    wb = load_workbook(workbook)
    eml = load_eml(eml)

    # Parameters for the function
    author = "spinneret.annotator.get_onto_gpt_annotation"
    dataset_element = eml.xpath("//dataset")[0]
    element_description = get_description(dataset_element)
    element_xpath = eml.getpath(dataset_element)
    predicate = "env_broad_scale"

    # Remove existing broad scale environmental context annotations if
    # overwrite is True, using a set of criteria that accurately define the
    # annotations to remove.
    if overwrite:
        wb = delete_annotations(
            workbook=wb,
            criteria={
                "element": "dataset",
                "element_xpath": "/eml:eml/dataset",
                "predicate": predicate,
                "author": author,
            },
        )

    # Skip if this element already has an annotation in the workbook, to
    # prevent duplicate annotations from being added.
    if has_annotation(wb, element_xpath, predicate):
        return wb

    # Reuse existing annotations for elements with identical tag names,
    # descriptions, and predicate labels, to reduce redundant processing.
    # Note this assumes semantic equivalence between elements with matching
    # tags and descriptions.
    annotations = get_annotation_from_workbook(
        workbook=wb,
        element=dataset_element.tag,
        description=element_description,
        predicate=predicate,
    )

    if annotations is None:
        # Get the broad scale environmental context annotations
        annotations = get_ontogpt_annotation(
            text=element_description,
            template=predicate,
            local_model=local_model,
            return_ungrounded=return_ungrounded,
        )

    # Add broad scale environmental context annotations to the workbook
    if annotations is not None:
        for annotation in annotations:
            row = initialize_workbook_row()
            row["package_id"] = get_package_id(eml)
            row["url"] = get_package_url(eml)
            row["element"] = dataset_element.tag
            if "id" in dataset_element.attrib:
                row["element_id"] = dataset_element.attrib["id"]
            else:
                row["element_id"] = pd.NA
            row["element_xpath"] = eml.getpath(dataset_element)
            row["context"] = get_subject_and_context(dataset_element)["context"]
            row["description"] = element_description
            row["subject"] = get_subject_and_context(dataset_element)["subject"]
            row["predicate"] = predicate
            row["predicate_id"] = (
                "https://genomicsstandardsconsortium.github.io/mixs/0000012/"
            )
            row["object"] = annotation["label"]
            row["object_id"] = annotation["uri"]
            row["author"] = author
            row["date"] = pd.Timestamp.now()
            row = pd.DataFrame([row], dtype=str)
            wb = pd.concat([wb, row], ignore_index=True)
        wb = delete_duplicate_annotations(wb)

    if output_path:
        write_workbook(wb, output_path)
    return wb


def add_env_local_scale_annotations_to_workbook(
    workbook: Union[str, pd.core.frame.DataFrame],
    eml: Union[str, etree._ElementTree],
    output_path: str = None,
    overwrite: bool = False,
    local_model: str = None,
    return_ungrounded: bool = False,
) -> pd.core.frame.DataFrame:
    """
    :param workbook: Either the path to the workbook to be annotated, or the
        workbook itself as a pandas DataFrame.
    :param eml: Either the path to the EML file corresponding to the workbook,
        or the EML file itself as an lxml etree.
    :param output_path: The path to write the annotated workbook.
    :param overwrite: If True, overwrite existing `local scale environmental
        context` annotations in the workbook, so a fresh set may be created.
    :param local_model: See `get_ontogpt_annotation` documentation for details.
    :param return_ungrounded: See `get_ontogpt_annotation` documentation for
        details.
    :returns: Workbook with local scale environmental context annotations.
    :notes: This function retrieves local scale environmental context
        annotations using OntoGPT, which requires setup and configuration
        described in the `get_ontogpt_annotation` function.
    """

    # Load the workbook and EML for processing
    wb = load_workbook(workbook)
    eml = load_eml(eml)

    # Parameters for the function
    dataset_element = eml.xpath("//dataset")[0]
    element_description = get_description(dataset_element)
    element_xpath = eml.getpath(dataset_element)
    predicate = "env_local_scale"

    # Set the author identifier for consistent reference below
    author = "spinneret.annotator.get_onto_gpt_annotation"

    # Remove existing local scale environmental context annotations if
    # overwrite is True, using a set of criteria that accurately define the
    # annotations to remove.
    if overwrite:
        wb = delete_annotations(
            workbook=wb,
            criteria={
                "element": "dataset",
                "element_xpath": "/eml:eml/dataset",
                "predicate": predicate,
                "author": author,
            },
        )

    # Skip if this element already has an annotation in the workbook, to
    # prevent duplicate annotations from being added.
    if has_annotation(wb, element_xpath, predicate):
        return wb

    # Reuse existing annotations for elements with identical tag names,
    # descriptions, and predicate labels, to reduce redundant processing.
    # Note this assumes semantic equivalence between elements with matching
    # tags and descriptions.
    annotations = get_annotation_from_workbook(
        workbook=wb,
        element=dataset_element.tag,
        description=element_description,
        predicate=predicate,
    )

    if annotations is None:
        # Get the local scale environmental context annotations
        annotations = get_ontogpt_annotation(
            text=element_description,
            template=predicate,
            local_model=local_model,
            return_ungrounded=return_ungrounded,
        )

    # Add local scale environmental context annotations to the workbook
    if annotations is not None:
        for annotation in annotations:
            row = initialize_workbook_row()
            row["package_id"] = get_package_id(eml)
            row["url"] = get_package_url(eml)
            row["element"] = dataset_element.tag
            if "id" in dataset_element.attrib:
                row["element_id"] = dataset_element.attrib["id"]
            else:
                row["element_id"] = pd.NA
            row["element_xpath"] = eml.getpath(dataset_element)
            row["context"] = get_subject_and_context(dataset_element)["context"]
            row["description"] = element_description
            row["subject"] = get_subject_and_context(dataset_element)["subject"]
            row["predicate"] = predicate
            row["predicate_id"] = (
                "https://genomicsstandardsconsortium.github.io/mixs/0000013/"
            )
            row["object"] = annotation["label"]
            row["object_id"] = annotation["uri"]
            row["author"] = author
            row["date"] = pd.Timestamp.now()
            row = pd.DataFrame([row], dtype=str)
            wb = pd.concat([wb, row], ignore_index=True)
        wb = delete_duplicate_annotations(wb)

    if output_path:
        write_workbook(wb, output_path)
    return wb


def add_env_medium_annotations_to_workbook(
    workbook: Union[str, pd.core.frame.DataFrame],
    eml: Union[str, etree._ElementTree],
    output_path: str = None,
    overwrite: bool = False,
    local_model: str = None,
    return_ungrounded: bool = False,
) -> pd.core.frame.DataFrame:
    """
    :param workbook: Either the path to the workbook to be annotated, or the
        workbook itself as a pandas DataFrame.
    :param eml: Either the path to the EML file corresponding to the workbook,
        or the EML file itself as an lxml etree.
    :param output_path: The path to write the annotated workbook.
    :param overwrite: If True, overwrite existing `environmental medium`
        annotations in the workbook, so a fresh set may be created.
    :param local_model: Required if `annotator` is "ontogpt". See
        `get_ontogpt_annotation` documentation for details.
    :param return_ungrounded: An option if `annotator` is "ontogpt". See
        `get_ontogpt_annotation` documentation for details.
    :returns: Workbook with environmental medium annotations."""

    # Parameters for the function
    predicate = "environmental material"

    # Load the workbook and EML for processing
    wb = load_workbook(workbook)
    eml = load_eml(eml)

    # Remove existing environmental medium annotations if overwrite is True,
    # using a set of criteria that accurately define the annotations to remove.
    if overwrite:
        wb = delete_annotations(
            workbook=wb,
            criteria={
                "element": "attribute",
                "element_xpath": "/attribute",
                "predicate": "environmental material",
                "author": "spinneret.annotator.get_ontogpt_annotation",
            },
        )

    # Iterate over EML attributes and add environmental medium annotations to
    # the workbook
    attributes = eml.xpath("//attribute")
    for attribute in attributes:
        attribute_element = attribute
        attribute_xpath = eml.getpath(attribute_element)
        attribute_description = get_description(attribute_element)

        # Skip if this element already has an annotation in the workbook, to
        # prevent duplicate annotations from being added.
        if has_annotation(wb, attribute_xpath, predicate):
            return wb

        # Reuse existing annotations for elements with identical tag names,
        # descriptions, and predicate labels, to reduce redundant processing.
        # Note this assumes semantic equivalence between elements with matching
        # tags and descriptions.
        annotations = get_annotation_from_workbook(
            workbook=wb,
            element=attribute_element.tag,
            description=attribute_description,
            predicate=predicate,
        )

        if annotations is None:
            # Get the environmental medium annotations from the annotator
            annotations = get_ontogpt_annotation(
                text=attribute_description,
                template="env_medium",
                local_model=local_model,
                return_ungrounded=return_ungrounded,
            )

        # And add the environmental medium annotations to the workbook
        if annotations is not None:
            for annotation in annotations:
                row = initialize_workbook_row()
                row["package_id"] = get_package_id(eml)
                row["url"] = get_package_url(eml)
                row["element"] = attribute_element.tag
                if "id" in attribute_element.attrib:
                    row["element_id"] = attribute_element.attrib["id"]
                else:
                    row["element_id"] = pd.NA
                row["element_xpath"] = attribute_xpath
                row["context"] = get_subject_and_context(attribute_element)["context"]
                row["description"] = attribute_description
                row["subject"] = get_subject_and_context(attribute_element)["subject"]
                row["predicate"] = predicate
                row["predicate_id"] = "http://purl.obolibrary.org/obo/ENVO_00010483"
                row["object"] = annotation["label"]
                row["object_id"] = annotation["uri"]
                row["author"] = "spinneret.annotator.get_ontogpt_annotation"
                row["date"] = pd.Timestamp.now()
                row = pd.DataFrame([row], dtype=str)
                wb = pd.concat([wb, row], ignore_index=True)
            wb = delete_duplicate_annotations(wb)

    if output_path:
        write_workbook(wb, output_path)
    return wb


def add_research_topic_annotations_to_workbook(
    workbook: Union[str, pd.core.frame.DataFrame],
    eml: Union[str, etree._ElementTree],
    output_path: str = None,
    overwrite: bool = False,
    local_model: str = None,
    return_ungrounded: bool = False,
) -> pd.core.frame.DataFrame:
    """
    :param workbook: Either the path to the workbook to be annotated, or the
        workbook itself as a pandas DataFrame.
    :param eml: Either the path to the EML file corresponding to the workbook,
        or the EML file itself as an lxml etree.
    :param output_path: The path to write the annotated workbook.
    :param overwrite: If True, overwrite existing `research topic` annotations
        in the workbook, so a fresh set may be created.
    :param local_model: See `get_ontogpt_annotation` documentation for details.
    :param return_ungrounded: See `get_ontogpt_annotation` documentation for
        details.
    :returns: Workbook with research topic annotations.
    :notes: This function retrieves research topic annotations using OntoGPT, which
        requires setup and configuration described in the
        `get_ontogpt_annotation` function.
    """

    # Load the workbook and EML for processing
    wb = load_workbook(workbook)
    eml = load_eml(eml)

    # Parameters for the function
    dataset_element = eml.xpath("//dataset")[0]
    element_description = get_description(dataset_element)
    element_xpath = eml.getpath(dataset_element)
    predicate = "research topic"

    # Set the author identifier for consistent reference below
    author = "spinneret.annotator.get_onto_gpt_annotation"

    # Remove existing research topic annotations if overwrite is True, using a set of
    # criteria that accurately define the annotations to remove.
    if overwrite:
        wb = delete_annotations(
            workbook=wb,
            criteria={
                "element": "dataset",
                "element_xpath": "/eml:eml/dataset",
                "predicate": "research topic",
                "author": author,
            },
        )

    # Skip if this element already has an annotation in the workbook, to
    # prevent duplicate annotations from being added.
    if has_annotation(wb, element_xpath, predicate):
        return wb

    # Reuse existing annotations for elements with identical tag names,
    # descriptions, and predicate labels, to reduce redundant processing.
    # Note this assumes semantic equivalence between elements with matching
    # tags and descriptions.
    annotations = get_annotation_from_workbook(
        workbook=wb,
        element=dataset_element.tag,
        description=element_description,
        predicate=predicate,
    )

    if annotations is None:
        # Get the research topic annotations
        annotations = get_ontogpt_annotation(
            text=element_description,
            template="research_topic",
            local_model=local_model,
            return_ungrounded=return_ungrounded,
        )

    # Add research topic annotations to the workbook
    if annotations is not None:
        for annotation in annotations:
            row = initialize_workbook_row()
            row["package_id"] = get_package_id(eml)
            row["url"] = get_package_url(eml)
            row["element"] = dataset_element.tag
            if "id" in dataset_element.attrib:
                row["element_id"] = dataset_element.attrib["id"]
            else:
                row["element_id"] = pd.NA
            row["element_xpath"] = eml.getpath(dataset_element)
            row["context"] = get_subject_and_context(dataset_element)["context"]
            row["description"] = element_description
            row["subject"] = get_subject_and_context(dataset_element)["subject"]
            row["predicate"] = predicate
            row["predicate_id"] = "http://vocabs.lter-europe.net/EnvThes/21604"
            row["object"] = annotation["label"]
            row["object_id"] = annotation["uri"]
            row["author"] = author
            row["date"] = pd.Timestamp.now()
            row = pd.DataFrame([row], dtype=str)
            wb = pd.concat([wb, row], ignore_index=True)
        wb = delete_duplicate_annotations(wb)

    if output_path:
        write_workbook(wb, output_path)
    return wb


def add_methods_annotations_to_workbook(
    workbook: Union[str, pd.core.frame.DataFrame],
    eml: Union[str, etree._ElementTree],
    output_path: str = None,
    overwrite: bool = False,
    local_model: str = None,
    return_ungrounded: bool = False,
) -> pd.core.frame.DataFrame:
    """
    :param workbook: Either the path to the workbook to be annotated, or the
        workbook itself as a pandas DataFrame.
    :param eml: Either the path to the EML file corresponding to the workbook,
        or the EML file itself as an lxml etree.
    :param output_path: The path to write the annotated workbook.
    :param overwrite: If True, overwrite existing `methods` annotations in the
        workbook, so a fresh set may be created.
    :param local_model: See `get_ontogpt_annotation` documentation for details.
    :param return_ungrounded: See `get_ontogpt_annotation` documentation for
        details.
    :returns: Workbook with methods annotations.
    :notes: This function retrieves methods annotations using OntoGPT, which
        requires setup and configuration described in the
        `get_ontogpt_annotation` function.
    """

    # Load the workbook and EML for processing
    wb = load_workbook(workbook)
    eml = load_eml(eml)

    # Parameters for the function
    # Get the methods annotations, if the methods element exists in the EML
    dataset_element = eml.xpath("//dataset")[0]
    methods_element = eml.xpath("//dataset/methods")
    if not methods_element:
        return wb
    element_description = get_description(methods_element[0])
    element_xpath = eml.getpath(dataset_element)
    predicate = "usesMethod"

    # Set the author identifier for consistent reference below
    author = "spinneret.annotator.get_onto_gpt_annotation"

    # Remove existing methods annotations if overwrite is True, using a set of
    # criteria that accurately define the annotations to remove.
    if overwrite:
        wb = delete_annotations(
            workbook=wb,
            criteria={
                "element": "dataset",
                "element_xpath": "/eml:eml/dataset",
                "predicate": predicate,
                "author": author,
            },
        )

    # Skip if this element already has an annotation in the workbook, to
    # prevent duplicate annotations from being added.
    if has_annotation(wb, element_xpath, predicate):
        return wb

    # Reuse existing annotations for elements with identical tag names,
    # descriptions, and predicate labels, to reduce redundant processing.
    # Note this assumes semantic equivalence between elements with matching
    # tags and descriptions.
    annotations = get_annotation_from_workbook(
        workbook=wb,
        element=dataset_element.tag,
        description=element_description,
        predicate=predicate,
    )

    if annotations is None:
        annotations = get_ontogpt_annotation(
            text=element_description,
            template="uses_method",
            local_model=local_model,
            return_ungrounded=return_ungrounded,
        )

    # Add methods annotations to the workbook. Note, methods annotations are
    # at the dataset level.
    if annotations is not None:
        for annotation in annotations:
            row = initialize_workbook_row()
            row["package_id"] = get_package_id(eml)
            row["url"] = get_package_url(eml)
            row["element"] = dataset_element.tag
            if "id" in dataset_element.attrib:
                row["element_id"] = dataset_element.attrib["id"]
            else:
                row["element_id"] = pd.NA
            row["element_xpath"] = eml.getpath(dataset_element)
            row["context"] = get_subject_and_context(dataset_element)["context"]
            row["description"] = element_description[0:500]  # don't need all of it
            row["subject"] = get_subject_and_context(dataset_element)["subject"]
            row["predicate"] = predicate
            row["predicate_id"] = (
                "http://ecoinformatics.org/oboe/oboe.1.2/oboe-core.owl#usesMethod"
            )
            row["object"] = annotation["label"]
            row["object_id"] = annotation["uri"]
            row["author"] = author
            row["date"] = pd.Timestamp.now()
            row = pd.DataFrame([row], dtype=str)
            wb = pd.concat([wb, row], ignore_index=True)
        wb = delete_duplicate_annotations(wb)

    if output_path:
        write_workbook(wb, output_path)
    return wb


def get_annotation_from_workbook(
    workbook: Union[str, pd.core.frame.DataFrame],
    element: str,
    description: str,
    predicate: str,
) -> Union[list, None]:
    """
    :param workbook: Either the path to the workbook to be annotated, or the
        workbook itself as a pandas DataFrame.
    :param element: The element to retrieve annotations for.
    :param description: The description of the element to retrieve annotations
        for.
    :param predicate: The predicate to retrieve annotations for.
    :returns: A list of dictionaries, each with the annotation keys
        `label` (same as `object` column in workbook), `uri` (same as
        `object_id` column in workbook). None if no annotations are found for
        the given element name.
    :notes: This function returns existing annotations from the workbook if
        the `element`, `description`, and `predicate` match, and the `object`
        and `object_id` are not empty. This is useful when one or more data
        entities have several attributes of different names but the same
        meaning.
    """
    wb = load_workbook(workbook)
    matching_rows = (
        (wb["element"] == element)
        & (wb["description"] == description)
        & (wb["predicate"] == predicate)
        & (wb["object"].notna())
        & (wb["object_id"].notna())
    )
    rows = wb[matching_rows].to_dict(orient="records")
    res = []
    if rows:
        for row in rows:
            row = {k: row[k] for k in ["object", "object_id"]}
            # Currently, workbook annotators reference the object as "label"
            # and the object_id as "uri", so we rename them here.
            row["label"] = row.pop("object")
            row["uri"] = row.pop("object_id")
            res.append(row)
        return res
    return None


def has_annotation(
    workbook: Union[str, pd.core.frame.DataFrame], element_xpath: str, predicate: str
) -> bool:
    """
    :param workbook: Either the path to the workbook to be annotated, or the
        workbook itself as a pandas DataFrame.
    :param element_xpath: The XPath of the element to check for annotations.
    :param predicate: The predicate to check for annotations.
    :returns: True if the `workbook` contains an `element_xpath` that has an
        annotation for the given `predicate`. False otherwise.
    """
    wb = load_workbook(workbook)
    matching_rows = (
        (wb["element_xpath"] == element_xpath)
        & (wb["predicate"] == predicate)
        & wb["predicate_id"].notna()
        & wb["object"].notna()
        & wb["object_id"].notna()
    )
    return bool(matching_rows.any())
