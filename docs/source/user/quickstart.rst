.. _quickstart:

Quickstart
==========

Welcome to the Quickstart guide! Whether you're a beginner or experienced developer, this guide helps you install the package, set up dependencies, and explore core functionalities.

Installation
------------

Currently, `spinneret` is only available on GitHub.  To install it, you need to have `pip <https://pip.pypa.io/en/stable/installation/>`_ installed.

Once pip is installed, you can install `spinneret` by running the following command in your terminal::

    $ pip install git+https://github.com/EDIorg/spinneret.git@main

For the latest development version::

    $ pip install git+https://github.com/EDIorg/spinneret.git@development


Adding QUDT Annotations to an EML File
---------------------------------------

.. code-block:: python

    from spinneret.datasets import get_example_eml_dir
    from spinneret.workbook import create, delete_unannotated_rows
    from spinneret.utilities import load_eml, write_eml
    from spinneret.annotator import add_qudt_annotations_to_workbook, \
        annotate_eml, get_qudt_annotation

Starting with an example EML file without QUDT annotations

.. code-block:: python

    eml_file = get_example_eml_dir() + "/edi.3.9.xml"

We initialize a "workbook" to store the annotations in a tabular format. The
workbook contents are later added to the EML file as annotation elements.

.. code-block:: python

    workbook = create(eml_file, elements=["attribute"])

A QUDT workbook "annotator" then searches through the EML for data entity
attributes with EML standard units (or custom units) that may be mapped to
QUDT equivalents via https://vocab.lternet.edu/webservice/unitsws.php, and adds
successful matches to the workbook.

.. code-block:: python

    eml = load_eml(eml_file)
    workbook = add_qudt_annotations_to_workbook(workbook, eml)
    workbook = delete_unannotated_rows(workbook)  # a little cleanup

We can now transfer the annotations from the workbook to the EML and write it
to file.

.. code-block:: python

    annotated_eml = annotate_eml(eml_file, workbook)
    output_path = "/Users/me/Data/edi.3.9.xml"  # or wherever you'd like
    write_eml(annotated_eml, output_path)

If you prefer a more rudimentary implementation, you can get QUDT label and URI
for specified input text.

.. code-block:: python

    get_qudt_annotation("degree")

    >>> [{'label': 'Degree', 'uri': 'http://qudt.org/vocab/unit/DEG'}]
