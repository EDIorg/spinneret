"""The main module"""

import os
from pathlib import Path
from requests import get, codes
from rdflib import Graph
import daiquiri
from soso.main import convert
from soso.strategies.eml import EML, get_encoding_format
from soso.utilities import delete_null_values, generate_citation_from_doi
from spinneret import workbook
from spinneret.annotator import annotate_workbook, annotate_eml
from spinneret.utilities import load_configuration
from spinneret.graph import create_graph
from spinneret.shadow import create_shadow_eml


logger = daiquiri.getLogger(__name__)


def create_workbooks(eml_dir: str, workbook_dir: str) -> None:
    """Create workbooks for each EML file in a directory
    :param eml_dir: Directory of EML files
    :param workbook_dir: Directory to save workbooks
    :return: None
    :notes: Workbooks will not be created if they already exist.
    """

    # A workbook is created for each EML file
    eml_files = os.listdir(eml_dir)
    eml_files = [f for f in eml_files if f.endswith(".xml")]  # Filter out non-XML files
    workbook_files = os.listdir(workbook_dir)
    workbook_pids = [wb.split("_")[0] for wb in workbook_files]

    # Iterate over EML files and create workbooks for each
    for eml_file in eml_files:

        # Continue if workbook already exists
        eml_pid = Path(eml_file).stem
        if eml_pid in workbook_pids:
            continue

        # Create workbook
        print(f"Creating workbook for {eml_file}")
        wb = workbook.create(
            eml_file=eml_dir + "/" + eml_file,
            elements=["dataset", "attribute"],
            path_out=workbook_dir,
        )


def annotate_workbooks(
    workbook_dir: str,
    eml_dir: str,
    annotator: str,
    output_dir: str,
    config_path: str,
    local_model: str = None,
    return_ungrounded: bool = False,
    sample_size: int = 1,
) -> None:
    """Create workbooks for each EML file in a directory

    :param workbook_dir: Directory of unannotated workbooks
    :param eml_dir: Directory of EML files corresponding to workbooks
    :param annotator: The annotator to use for grounding. Options are "ontogpt"
        and "bioportal". OntoGPT requires setup and configuration described in
        the `get_ontogpt_annotation` function. Similarly, BioPortal requires
        an API key and is described in the `get_bioportal_annotation` function.
    :param output_dir: Directory to save annotated workbooks
    :param config_path: Path to configuration file
    :param local_model: See `get_ontogpt_annotation` documentation for details.
    :param return_ungrounded: See `get_ontogpt_annotation` documentation for
        details.
    :param sample_size: Executes multiple replicates of the annotation request
        to reduce variability of outputs. Variability is inherent in OntoGPT.
    :return: None
    :notes: Annotated workbooks will not be created if they already exist.
    """

    # Load BioPortal API key
    load_configuration(config_path)

    # An annotated workbook is created for unannotated workbook file
    workbook_files = os.listdir(workbook_dir)
    workbook_files = [
        f for f in workbook_files if f.endswith(".tsv")
    ]  # Filter out non-TSV files
    output_files = os.listdir(output_dir)
    output_files = [f for f in output_files if f.endswith(".tsv")]

    # Iterate over EML files and create workbooks for each
    for workbook_file in workbook_files:

        # Continue if annotated workbook already exists
        workbook_file_annotated = workbook_file.replace(".tsv", "_annotated.tsv")
        if workbook_file_annotated in output_files:
            continue

        # Match EML file to workbook file
        eml_pid = workbook_file.split("_")[0]
        eml_file = eml_pid + ".xml"
        if not os.path.exists(eml_dir + "/" + eml_file):
            print(f"Could not find EML file for {workbook_file}")
            continue

        # Create annotated workbook
        logger.info(f"Creating annotated workbook for {workbook_file}")
        print(f"Creating annotated workbook for {workbook_file}")
        annotate_workbook(
            workbook_path=workbook_dir + "/" + workbook_file,
            eml_path=eml_dir + "/" + eml_file,
            annotator=annotator,
            output_path=output_dir + "/" + workbook_file_annotated,
            local_model=local_model,
            return_ungrounded=return_ungrounded,
            sample_size=sample_size,
        )


def annotate_eml_files(workbook_dir: str, eml_dir: str, output_dir: str) -> None:
    """Create workbooks for each EML file in a directory

    :param workbook_dir: Directory of annotated workbooks
    :param eml_dir: Directory of unannotated EML files
    :output_dir: Directory to save annotated EML files
    :return: None
    :notes: Annotated EML files will not be created if they already exist.
    """

    # An annotated EML file is created for each annotated workbook file
    workbook_files = os.listdir(workbook_dir)
    eml_files = os.listdir(eml_dir)
    eml_files = [f for f in eml_files if f.endswith(".xml")]  # Filter out non-XML files

    # Iterate over workbook files and create annotated EML for each
    for workbook_file in workbook_files:

        # Continue if the EML file does not exist or is already annotated
        eml_path = eml_dir + "/" + workbook_file.split("_")[0] + ".xml"
        if not os.path.exists(eml_path):
            continue
        eml_path_annotated = output_dir + "/" + workbook_file.split("_")[0] + ".xml"
        if os.path.exists(eml_path_annotated):
            continue

        # Create annotated EML file
        print(f"Creating annotated EML file for {eml_path}")
        annotate_eml(
            eml=eml_path,
            workbook=workbook_dir + "/" + workbook_file,
            output_path=eml_path_annotated,
        )


# pylint: disable=too-many-locals
def create_soso_files(eml_dir: str, output_dir: str) -> None:
    """Create SOSO files for each EML file in a directory

    :param eml_dir: Directory of annotated EML files
    :param output_dir: Directory to save SOSO files
    :return: None
    :notes: SOSO files will not be created if they already exist.
    """

    # A SOSO file is created for each EML file
    eml_files = os.listdir(eml_dir)
    eml_files = [f for f in eml_files if f.endswith(".xml")]  # Filter out non-XML files
    soso_files = os.listdir(output_dir)

    # Iterate over EML files and create SOSO files for each
    for eml_file in eml_files:

        # Continue if SOSO file already exists
        eml_pid = Path(eml_file).stem
        soso_file = eml_pid + ".json"
        if soso_file in soso_files:
            continue
        print(f"Creating SOSO file for {eml_file}")

        # Add properties that can't be derived from the EML record
        scope, identifier, revision = eml_pid.split(".")
        # url
        url = (
            "https://portal.edirepository.org/nis/mapbrowse?scope="
            + scope
            + "&identifier="
            + identifier
            + "&revision="
            + revision
        )
        # @id
        dataset_id = url
        # is_accessible_for_free
        is_accessible_for_free = True
        # doi
        doi_uri = (
            f"https://pasta.lternet.edu/package/doi/eml/{scope}/{identifier}/{revision}"
        )
        doi = get(doi_uri, timeout=10)
        if doi.status_code == codes.ok:  # pylint: disable=no-member
            doi = doi.text
            doi = "https://doi.org/" + doi.split(":")[1]  # URL format
        else:
            doi = None
        # identifier
        if doi is not None:
            identifier = {  # DOI is more informative than the packageId
                "@id": doi,
                "@type": "PropertyValue",
                "propertyID": "https://registry.identifiers.org/registry/doi",
                "value": doi.split("https://doi.org/")[1],
                "url": doi,
            }
        else:
            identifier = None
        # citation
        if doi is not None:
            citation = generate_citation_from_doi(doi, style="apa", locale="en-US")
        else:
            citation = None
        provider = {"@id": "https://edirepository.org"}
        publisher = {"@id": "https://edirepository.org"}

        # Modify the get_subject_of method to add the missing contentUrl
        def get_subject_of(self):
            encoding_format = get_encoding_format(self.metadata)
            date_modified = self.get_date_modified()
            if encoding_format and date_modified:
                file_name = self.file.split("/")[-1]
                subject_of = {
                    "@type": "DataDownload",
                    "name": "EML metadata for dataset",
                    "description": "EML metadata describing the dataset",
                    "encodingFormat": encoding_format,
                    "contentUrl": (
                        "https://pasta.lternet.edu/package/metadata/eml/"
                        + file_name.split(".")[0]
                        + "/"
                        + file_name.split(".")[1]
                        + "/"
                        + file_name.split(".")[2]
                    ),
                    "dateModified": date_modified,
                }
                return delete_null_values(subject_of)
            return None

        EML.get_subject_of = get_subject_of  # Override the method

        # Call the convert function with the additional properties
        additional_properties = {
            "url": url,
            "version": revision,
            "isAccessibleForFree": is_accessible_for_free,
            "citation": citation,
            "provider": provider,
            "publisher": publisher,
            "identifier": identifier,
            "@id": dataset_id,
        }
        json_ld = convert(
            file=eml_dir + "/" + eml_file, strategy="EML", **additional_properties
        )

        # Reformat the JSON-LD for readability and write to file
        with open(output_dir + "/" + soso_file, "w", encoding="utf-8") as fp:
            fp.write(json_ld)


def create_shadow_eml_files(eml_dir: str, output_dir: str) -> None:
    """Create shadow EML files for each EML file in a directory

    :param eml_dir: Directory of EML files
    :param output_dir: Directory to save shadow EML files
    :return: None
    :notes: Shadow EML files will not be created if they already exist.
    """

    # A shadow EML file is created for each EML file
    eml_files = os.listdir(eml_dir)
    eml_files = [f for f in eml_files if f.endswith(".xml")]  # Filter out non-XML files
    shadow_files = os.listdir(output_dir)

    # Iterate over EML files and create shadow EML files for each
    for eml_file in eml_files:

        # Continue if shadow file already exists
        eml_pid = Path(eml_file).stem
        shadow_file = eml_pid + ".xml"
        if shadow_file in shadow_files:
            continue

        # Create shadow EML file
        print(f"Creating shadow EML file for {eml_file}")
        create_shadow_eml(
            eml_path=eml_dir + "/" + eml_file,
            output_path=output_dir + "/" + shadow_file,
        )


def create_kgraph(soso_dir: str, vocabulary_dir: str) -> Graph:
    """Create a Knowledge Graph from SOSO files and vocabularies

    :param soso_dir: Directory of SOSO files
    :param vocabulary_dir: Directory of vocabulary files
    :return: Knowledge Graph"""

    # Get list of SOSO and vocabulary files
    soso_files = [soso_dir + "/" + f for f in os.listdir(soso_dir)]
    soso_files = [
        f for f in soso_files if f.endswith(".json")
    ]  # Filter out non-JSON files
    vocabulary_files = [vocabulary_dir + "/" + f for f in os.listdir(vocabulary_dir)]
    vocabulary_files = [
        f for f in vocabulary_files if f.endswith(".ttl") or f.endswith(".owl")
    ]  # Filter out non-TTL and non-OWL files

    # Load knowledge graph
    kgraph = create_graph(metadata_files=soso_files, vocabulary_files=vocabulary_files)

    return kgraph


if __name__ == "__main__":

    # create_workbooks(
    #     eml_dir="/Users/csmith/Data/kgraph/eml/raw",
    #     workbook_dir="/Users/csmith/Data/kgraph/workbook/raw",
    # )

    # annotate_workbooks(
    #     workbook_dir="/Users/csmith/Data/kgraph/workbook/raw",
    #     eml_dir="/Users/csmith/Data/kgraph/eml/raw",
    #     output_dir="/Users/csmith/Data/kgraph/workbook/annotated",
    #     config_path="/Users/csmith/Code/spinneret_EDIorg/spinneret/config.json",
    # )

    # annotate_eml_files(
    #     workbook_dir="/Users/csmith/Data/kgraph/workbook/annotated",
    #     eml_dir="/Users/csmith/Data/kgraph/eml/raw",
    #     output_dir="/Users/csmith/Data/kgraph/eml/annotated",
    # )

    # create_shadow_eml_files(
    #     eml_dir="/Users/csmith/Data/kgraph/eml/annotated",
    #     output_dir="/Users/csmith/Data/kgraph/eml/shadow",
    # )

    # create_soso_files(
    #     eml_dir="/Users/csmith/Data/kgraph/eml/shadow",
    #     output_dir="/Users/csmith/Data/kgraph/soso/raw",
    # )

    # g = create_kgraph(
    #     soso_dir="/Users/csmith/Data/kgraph/soso/annotated",
    #     vocabulary_dir="/Users/csmith/Data/kgraph/vocab",
    # )
    # # Serialize to file
    # g.serialize(
    #     destination="/Users/csmith/Data/kgraph/kgraph/edi_kgraph_top_20.ttl",
    #     format="turtle"
    # )

    pass
