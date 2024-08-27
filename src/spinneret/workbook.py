"""The workbook module"""

from uuid import uuid4
from lxml import etree
import pandas as pd


def create(
    eml_file: str, elements: list, base_url: str, path_out: str = False
) -> pd.core.frame.DataFrame:
    """Create an annotation workbook from an EML file

    :param eml_file: Path to a single EML file
    :param elements:    List of EML elements to include in the workbook. Can be
                        one or more of: 'dataset', 'dataTable', 'otherEntity',
                        'spatialVector', 'spatialRaster', 'storedProcedure',
                        'view', 'attribute'.
    :param base_url:    Base URL of data package landing pages which is combined
                        with the EML root attribute value 'packageId' to create
                        link to data packages listed in the workbook. This
                        fully formed URL is useful in the annotation process by
                        linking the data curator to the full human readable
                        data package landing page.
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
    eml = etree.parse(eml_file)
    package_id = eml.xpath("./@packageId")[0]
    url = base_url + package_id
    res = []
    for element in elements:
        for e in eml.xpath(".//" + element):
            subcon = get_subject_and_context(e)
            row = [
                package_id,
                url,
                element,
                str(uuid4()),
                eml.getpath(e),
                subcon["context"],
                get_description(e),
                subcon["subject"],
                "",  # predicate
                "",  # predicate id
                "",  # object
                "",  # object_id
                "",  # author
                "",  # date
                "",  # comment
            ]
            res.append(row)
    colnames = [
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
    res = pd.DataFrame(res, columns=colnames)
    if path_out:
        path_out = path_out + "/" + package_id + "_annotation_workbook.tsv"
        res.to_csv(path_out, sep="\t", index=False, mode="x")
    return res


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
        abstract = etree.tostring(abstract[0], encoding="utf-8", method="text")
        abstract = abstract.decode("utf-8").strip()
        keywords = element.xpath(".//keyword")
        keywords = [k.text for k in keywords]
        description = abstract + " " + " ".join(keywords)
    elif element.tag in entities:
        description = element.findtext(".//entityName")
    elif element.tag in "attribute":
        description = element.findtext(".//attributeDefinition")
    else:
        description = None
    return description
