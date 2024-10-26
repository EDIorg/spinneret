"""Test shadow code"""

from lxml import etree
from spinneret.shadow import convert_userid_to_url, create_shadow_eml
from spinneret.datasets import get_example_eml_dir
from spinneret.utilities import is_url, load_eml


def test_convert_userid_to_url():
    """Test convert_userid_to_url"""

    # Elements with missing directory attribute are not processed
    data = """
    <root>
        <userId>user1</userId>
    </root>
    """
    eml = etree.ElementTree(etree.fromstring(data))
    res = convert_userid_to_url(eml)
    assert res.xpath("//userId")[0].text == "user1"

    # If the directory attribute is not a URL, then the element is not processed
    data = """
    <root>
        <userId directory="not_a_url">user1</userId>
    </root>
    """
    eml = etree.ElementTree(etree.fromstring(data))
    res = convert_userid_to_url(eml)
    assert res.xpath("//userId")[0].text == "user1"

    # If the directory attribute is a URL, then the element is processed. This
    # also tests that the value is converted to a URL if it is not already a URL.
    data = """
    <root>
        <userId directory="https://example.com/">user1</userId>
    </root>
    """
    eml = etree.ElementTree(etree.fromstring(data))
    res = convert_userid_to_url(eml)
    assert res.xpath("//userId")[0].text == "https://example.com/user1"

    # If the value is already a URL, then the element is returned as is
    data = """
    <root>
        <userId directory="https://example.com/">https://example.com/user1</userId>
    </root>
    """
    eml = etree.ElementTree(etree.fromstring(data))
    res = convert_userid_to_url(eml)
    assert res.xpath("//userId")[0].text == "https://example.com/user1"

    # Check that the value is returned as is if the directory is not a URL but
    # the value is a URL
    data = """
    <root>
        <userId directory="not_a_url">https://example.com/user1</userId>
    </root>
    """
    eml = etree.ElementTree(etree.fromstring(data))
    res = convert_userid_to_url(eml)
    assert res.xpath("//userId")[0].text == "https://example.com/user1"


def test_create_shadow_eml(tmp_path):
    """Test create_shadow_eml"""
    eml_file = get_example_eml_dir() + "/" + "edi.3.9.xml"
    output_file = str(tmp_path) + "/edi.3.9_shadow.xml"

    create_shadow_eml(eml_path=eml_file, output_path=output_file)

    eml = load_eml(eml_file)
    shadow_eml = load_eml(output_file)

    # Check that the shadow EML is different from the original EML
    assert etree.tostring(eml) != etree.tostring(shadow_eml)

    # Check that at least one of the userId elements in the original EML are
    # not URLs
    user_ids = eml.xpath("//userId")
    for element in user_ids:
        if not is_url(element.text):
            break
    else:
        assert False
    # Check that all userId elements have been converted to URLs
    shadow_user_ids = shadow_eml.xpath("//userId")
    for element in shadow_user_ids:
        assert is_url(element.text)
