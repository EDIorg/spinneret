"""The workbook module"""

from lxml import etree
import pandas as pd
from spinneret.utilities import delete_empty_tags, load_eml, write_workbook


def create(
    eml_file: str, elements: list, env: str = "production", path_out: str = False
) -> pd.core.frame.DataFrame:
    """Create an annotation workbook from an EML file

    :param eml_file: Path to a single EML file
    :param elements:    List of EML elements to include in the workbook. Can be
                        one or more of: 'dataset', 'dataTable', 'otherEntity',
                        'spatialVector', 'spatialRaster', 'storedProcedure',
                        'view', 'attribute'.
    :param env: The environment to use for the base URL. Options are:
        'production', 'staging', 'development'.
    :param path_out:    Path to a directory where the workbook will be written.
                        Will result in a file
                        '[packageId]_annotation_workbook.tsv'.
    :returns:   DataFrame of the annotation workbook with columns:

                * `package_id`: Data package identifier listed in the EML at
                  the xpath attribute `packageId`
                * `url`: Link to the data package landing page corresponding to
                  'package_id'
                * `element`: Element to be annotated
                * `element_id`: UUID assigned at the time of workbook creation
                * `element_xpath`: xpath of element to be annotated
                * `context`: The broader context in which the subject is found.
                  When the subject is a dataset the context is the packageId.
                  When the subject is a data object/entity, the context is
                  `dataset`. When the subject is an attribute, the context is
                  the data object/entity the attribute is apart of.
                * `subject`: The subject of annotation
                * `predicate`: The label of the predicate relating the subject
                  to the object
                * `predicate_id`: The identifier of the predicate. Typically,
                  this is a URI/IRI.
                * `object`: The label of the object
                * `object_id`: The identifier of the object. Typically, this
                  is a URI/IRI.
                * `author`: Identifier of the data curator authoring the
                  annotation. Typically, this value is an ORCiD.
                * `date`: Date of the annotation. Can be helpful when
                  revisiting annotations.
                * `comment`: Comments related to the annotation. Can be useful
                  when revisiting an annotation at a later date.
    """
    eml = load_eml(eml_file)
    eml = delete_empty_tags(eml)
    wb = pd.DataFrame(columns=list_workbook_columns())  # initialize workbook
    for element in elements:
        for e in eml.xpath(".//" + element):
            row = initialize_workbook_row()
            row["package_id"] = get_package_id(eml)
            row["url"] = get_package_url(eml, env)
            row["element"] = element
            if "id" in e.attrib:
                row["element_id"] = e.attrib["id"]
            else:
                row["element_id"] = pd.NA
            row["element_xpath"] = eml.getpath(e)
            row["context"] = get_subject_and_context(e)["context"]
            row["description"] = get_description(e)
            row["subject"] = get_subject_and_context(e)["subject"]
            wb.loc[len(wb)] = row  # append row to workbook
    if path_out:
        path_out = path_out + "/" + get_package_id(eml) + "_annotation_workbook.tsv"
        write_workbook(wb, path_out)
    return wb


def get_subject_and_context(element: etree._Element) -> dict:
    """Get subject and context values for a given element

    This function is called by 'workbook.create' to get the subject and
    context values. See 'workbook.create' for explanation of parameters.

    :param element: The EML element to be annotated.
    :returns:   Dictionary with keys 'subject' and 'context' and values as the
                subject and context of the element.
    :notes: Values for the 'subject' and 'context' of each annotatable element
            is defined on a case-by-case basis. This approach is taken because
            a generalizable pattern to derive recognizable and meaningful
            values for these fields is difficult since annotatable elements
            (specified by the EML schema) aren't constrained to leaf nodes
            with text values.
    """
    entities = [
        "dataTable",
        "otherEntity",
        "spatialVector",
        "spatialRaster",
        "storedProcedure",
        "view",
    ]
    if element.tag in "dataset":
        subject = "dataset"
        p = element.getparent()
        context = p.xpath("./@packageId")[0]
    elif element.tag in entities:
        subject = element.findtext(".//objectName")
        context = "dataset"
    elif element.tag in "attribute":
        subject = element.findtext(".//attributeName")
        entity = list(element.iterancestors(entities))
        context = entity[0].findtext(".//objectName")
    else:
        subject = None
        context = None
    res = {"subject": subject, "context": context}
    return res


def get_description(element: etree._Element) -> str:
    """Get the description of an element

    :param element: The EML element to be annotated.
    :returns:   The description of the element.
    """
    entities = [
        "dataTable",
        "otherEntity",
        "spatialVector",
        "spatialRaster",
        "storedProcedure",
        "view",
    ]
    if element.tag in "dataset":
        # Add abstract and keywords, they are descriptive of the entire dataset
        abstract = element.xpath("./abstract")
        if len(abstract) != 0:  # abstract is optional
            abstract = etree.tostring(abstract[0], encoding="utf-8", method="text")
            abstract = abstract.decode("utf-8").strip()
        else:
            abstract = ""
        keywords = element.xpath(".//keyword")
        if len(keywords) != 0:  # keywords are optional
            keywords = [k.text for k in keywords]
        else:
            keywords = ""
        description = abstract + " ".join(keywords)
    elif element.tag in entities:
        description = element.findtext(".//entityName")
    elif element.tag in "attribute":
        description = element.findtext(".//attributeDefinition")
    elif element.tag in "methods":
        methods = etree.tostring(element, encoding="utf-8", method="text")
        description = methods.decode("utf-8").strip()
    else:
        description = None
    return description


def list_workbook_columns() -> list:
    """
    :returns: A list of the columns in the workbook.
    """
    res = [
        "package_id",
        "url",
        "element",
        "element_id",
        "element_xpath",
        "context",
        "description",
        "subject",
        "predicate",
        "predicate_id",
        "object",
        "object_id",
        "author",
        "date",
        "comment",
    ]
    return res


def initialize_workbook_row() -> pd.core.series.Series:
    """Initialize a row for the annotation workbook
    :returns:   A pandas Series with the initialized row
    """
    row = dict.fromkeys(list_workbook_columns(), pd.NA)
    return pd.Series(row)


def get_package_id(eml: etree._ElementTree) -> str:
    """
    :param eml: The EML file as an lxml etree object
    :returns: The packageId of the EML file
    """
    package_id = eml.xpath("./@packageId")[0]
    return package_id


def get_package_url(eml: etree._ElementTree, env: str = "production") -> str:
    """
    :param eml: The EML file as an lxml etree object
    :param env: The environment to use for the base URL. Options are:
        'production', 'staging', 'development'.
    :returns: The URL to the data package landing page
    """
    if env == "staging":
        base_url = "https://portal-s.edirepository.org/nis/metadataviewer?packageid="
    elif env == "development":
        base_url = "https://portal-d.edirepository.org/nis/metadataviewer?packageid="
    else:
        base_url = "https://portal.edirepository.org/nis/metadataviewer?packageid="
    package_id = get_package_id(eml)
    url = base_url + package_id
    return url


def delete_duplicate_annotations(
    workbook: pd.core.frame.DataFrame,
) -> pd.core.frame.DataFrame:
    """
    :param workbook: The annotation workbook
    :returns: The workbook with duplicate annotations removed
    :notes: The function removes duplicate annotations based on the
        following columns: `element_xpath`, `object`, `object_id`, `date`. The
        most recent annotation is preferred to allow improvements to other
        fields set by the annotator.

    """
    wb = workbook.sort_values("date", ascending=False)
    wb = wb.drop_duplicates(
        subset=[
            "element_xpath",
            "object",
            "object_id",
        ],
        keep="first",
    )
    return wb


def delete_annotations(
    workbook: pd.core.frame.DataFrame, criteria: dict
) -> pd.core.frame.DataFrame:
    """
    :param workbook: The workbook to delete rows of annotations from.
    :param criteria: A dictionary of key-value pairs to define rows to delete.
        Each key corresponds to a column in the workbook and each value is a
        string to match in the column.
    :returns: The workbook with annotations deleted corresponding to the
        criteria.
    :notes: A matching row must contain all key-value pairs in the criteria
        dictionary to be deleted. Matching is case-sensitive. Partial
        matches are supported.
    """
    wb = workbook.copy()
    filtered_wb = wb[
        ~wb[list(criteria)]
        .apply(lambda x: x.str.contains(criteria[x.name]))
        .all(axis=1)
    ]
    return filtered_wb
