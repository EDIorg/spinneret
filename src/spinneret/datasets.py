"""Access built-in data objects"""
import importlib.resources


def get_example_eml_dir():
    """Get path to directory of EML files for example demonstrations

    Returns
    -------
    Path to directory of EML files.

    Examples
    --------
    >>> get_example_eml_dir()
    """
    res = str(importlib.resources.files("spinneret.data")) + "/eml"
    return res
