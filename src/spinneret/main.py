"""The main module"""

import os
from pathlib import Path
from spinneret import workbook


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


if __name__ == "__main__":

    create_workbooks(
        eml_dir="/Users/csmith/Data/kgraph/eml/raw",
        workbook_dir="/Users/csmith/Data/kgraph/workbook/raw",
    )
