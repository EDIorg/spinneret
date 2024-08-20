"""The datasets module"""

import importlib.resources


def get_example_eml_dir():
    """
    :returns:   Path to directory of EML files for use in examples
    """
    res = str(importlib.resources.files("spinneret.data")) + "/eml"
    return res
