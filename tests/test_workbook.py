"""Test workbook code"""

import os
import tempfile
import pandas as pd
from spinneret import workbook
from spinneret import datasets


def test_create():
    """Test workbook creation and attributes"""

    # A workbook is created for each EML file
    eml_dir = datasets.get_example_eml_dir()
    eml_file = eml_dir + "/" + os.listdir(eml_dir)[0]
    with tempfile.TemporaryDirectory() as tmpdir:
        wb = workbook.create(
            eml_file=eml_file,
            elements=["dataset", "dataTable", "otherEntity", "attribute"],
            base_url="https://portal.edirepository.org/nis/metadataviewer?packageid=",
            path_out=tmpdir,
        )
        eml_file_name = os.path.basename(eml_file)
        package_id = os.path.splitext(eml_file_name)[0]
        wb_path = tmpdir + "/" + package_id + "_annotation_workbook.tsv"
        assert os.path.isfile(wb_path)
        assert isinstance(wb, pd.core.frame.DataFrame)
        assert len(wb.package_id.unique()) == 1

        # Test workbook attributes against fixture
        wbf = pd.read_csv("tests/edi.3.9_annotation_workbook.tsv", sep="\t").fillna("")
        cols = wb.columns.to_list()
        for c in cols:
            if c != "element_id":  # new UUIDs won't match the fixture
                assert sorted(wb[c].unique()) == sorted(wbf[c].unique())
