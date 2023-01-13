"""Workbook related operations"""
import os
from uuid import uuid4
from lxml import etree
import pandas as pd


def create(eml, elements, base_url, path_out=False):
    """Create an annotation workbook from EML files

    Parameters
    ----------
    eml : str
        Path to a directory containing only EML files or a path to a single
        EML file.
    elements : list of str
        List of EML elements to include in the workbook. Can be one or more
        of: 'dataset', 'dataTable', 'otherEntity', 'spatialVector',
        'spatialRaster', 'storedProcedure', 'view', 'attribute'.
    base_url : str
        Base URL of data package landing pages which is combined with the
        EML root attribute value 'packageId' to create link to data packages
        listed in the workbook. This fully formed URL is useful in the
        annotation process by linking the data curator to the full human
        readable data package landing page.
    path_out : str
        Path to a directory where the workbook will be written. Will result in
        a file 'annotation_workbook.tsv'.

    Returns
    -------
    pandas.core.frame.DataFrame
        Columns:
            package_id:
                Data package identifier listed in the EML at the xpath
                './@packageId'
            url:
                Link to the data package landing page corresponding to
                'package_id'
            element:
                Element to be annotated
            element_id:
                UUID assigned at the time of workbook creation
            element_xpath:
                xpath of element to be annotated
            context:
                The broader context in which the subject is found. When the
                subject is a dataset the context is the packageId. When the
                subject is a data object/entity, the context is 'dataset'.
                When the subject is an attribute, the context is the data
                object/entity the attribute is apart of.
            subject:
                The subject of annotation
            predicate:
                The label of the predicate relating the subject to the object
            predicate_id:
                The identifier of the predicate. Typically, this is a URI/IRI.
            object:
                The label of the object
            object_id:
                The identifier of the object. Typically, this is a URI/IRI.
            author:
                Identifier of the data curator authoring the annotation.
                Typically, this value is an ORCiD.
            date:
                Date of the annotation. Can be helpful when revisiting
                annotations.
            comment:
                Comments related to the annotation. Can be useful when
                revisiting an annotation at a later date.

    Examples
    --------
    >>> from spinneret import workbook
    Create a workbook from a directory of EML files
    >>> wb = workbook.create(
    ...     eml=datasets.get_example_eml_dir(),
    ...     elements=['dataset', 'dataTable', 'otherEntity', 'attribute'],
    ...     base_url='https://portal.edirepository.org/nis/metadataviewer?packageid='
    ... )
    >>> wb.info(verbose=True)
    Typically, you'll want to write the workbook to file by providing a
    'path_out' argument.
    """
    if os.path.isdir(eml):
        eml = [eml + "/" + p for p in os.listdir(eml)]
    else:
        eml = [eml]
    res = []
    for f in eml:
        df = elements_to_df(f, elements, base_url)
        res.append(df)
    res = pd.concat(res)
    if path_out:
        path_out = path_out + "/" + "annotation_workbook.tsv"
        res.to_csv(path_out, sep="\t", index=False, mode="x")
    return res


def elements_to_df(eml, elements, base_url):
    """Convert a single EML file to a dataframe

    This function is called by 'workbook.create()' to form a list of dataframes,
    one for each EML file, then concatenate into the full workbook dataframe.

    Parameters
    ----------
    eml : str
        See parameter definition in 'workbook.create()'
    elements : str
        See parameter definition in 'workbook.create()'
    base_url : str
        See parameter definition in 'workbook.create()'

    Returns
    -------
    pandas.core.frame.DataFrame
        See column definitions in 'workbook.create()'
    """
    eml = etree.parse(eml)
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
    return res


def get_subject_and_context(element):
    """Get subject and context values for a given element

    This function is called by 'elements_to_df()' to get the subject and
    context values. See 'workbook.create()' for explanation of

    Parameters
    ----------
    element : lxml.etree._Element
        The EML element to be annotated.

    Returns
    -------
    dict of str
        subject: The subject of the element
        context: The context of the element

    Notes
    -----
    Values for the 'subject' and 'context' of each annotatable element is
    defined on a case-by-case basis. This approach is taken because a
    generalizable pattern to derive recognizable and meaningful values for
    these fields is difficult since annotatable elements (specified by the EML
    schema) aren't constrained to leaf nodes with text values.
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
    res = {"subject": subject, "context": context}
    return res
