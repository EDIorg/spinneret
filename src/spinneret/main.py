"""The main module"""

import os
from pathlib import Path
from spinneret import workbook
from spinneret.annotator import annotate_workbook, annotate_eml
from spinneret.utilities import load_configuration


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
            base_url="https://portal.edirepository.org/nis/metadataviewer?packageid=",
            path_out=workbook_dir,
        )


def annotate_workbooks(workbook_dir: str, output_dir: str, config_path: str) -> None:
    """Create workbooks for each EML file in a directory

    :param workbook_dir: Directory of unannotated workbooks
    :param output_dir: Directory to save annotated workbooks
    :param config_path: Path to configuration file
    :return: None
    :notes: Annotated workbooks will not be created if they already exist.
    """

    # Load BioPortal API key
    load_configuration(config_path)

    # An annotated workbook is created for unannotated workbook file
    workbook_files = os.listdir(workbook_dir)
    workbook_files = [f for f in workbook_files if f.endswith(".tsv")]  # Filter out non-TSV files
    output_files = os.listdir(output_dir)
    output_files = [f for f in output_files if f.endswith(".tsv")]

    # Iterate over EML files and create workbooks for each
    for workbook_file in workbook_files:

        # Continue if annotated workbook already exists
        workbook_file_annotated = workbook_file.replace(".tsv", "_annotated.tsv")
        if workbook_file_annotated in output_files:
            continue

        # Create annotated workbook
        print(f"Creating annotated workbook for {workbook_file}")
        annotate_workbook(
            workbook_path=workbook_dir + "/" + workbook_file,
            output_path=output_dir + "/" + workbook_file_annotated,
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
            eml_path=eml_path,
            workbook_path=workbook_dir + "/" + workbook_file,
            output_path=eml_path_annotated,
        )


if __name__ == "__main__":

    # create_workbooks(
    #     eml_dir="/Users/csmith/Data/kgraph/eml/raw",
    #     workbook_dir="/Users/csmith/Data/kgraph/workbook/raw",
    # )

    # annotate_workbooks(
    #     workbook_dir="/Users/csmith/Data/kgraph/workbook/raw",
    #     output_dir="/Users/csmith/Data/kgraph/workbook/annotated",
    #     config_path="/Users/csmith/Code/spinneret_EDIorg/spinneret/config.json",
    # )

    annotate_eml_files(
        workbook_dir="/Users/csmith/Data/kgraph/workbook/annotated",
        eml_dir="/Users/csmith/Data/kgraph/eml/raw",
        output_dir="/Users/csmith/Data/kgraph/eml/annotated",
    )

