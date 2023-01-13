"""Test workbook code"""
import os
import tempfile
import pandas as pd
from spinneret import workbook
from spinneret import datasets


def test_create():
    """Test workbook creation and attributes"""

    # A workbook is typically created from a directory of EML files
    with tempfile.TemporaryDirectory() as tmpdir:
        wb = workbook.create(
            eml=datasets.get_example_eml_dir(),
            elements=["dataset", "dataTable", "otherEntity", "attribute"],
            base_url="https://portal.edirepository.org/nis/metadataviewer?packageid=",
            path_out=tmpdir,
        )
        wb_path = tmpdir + "/" + "annotation_workbook.tsv"
        assert os.path.isfile(wb_path)
        assert isinstance(wb, pd.core.frame.DataFrame)
        assert len(wb.package_id.unique()) == 3

        # Test workbook attributes against fixture
        wbf = pd.read_csv("tests/annotation_workbook.tsv", sep="\t").fillna("")
        cols = wb.columns.to_list()
        for c in cols:
            if c != "element_id":  # new UUIDs won't match the fixture
                assert sorted(wb[c].unique()) == sorted(wbf[c].unique())
