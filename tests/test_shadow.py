"""Test shadow code"""

from lxml import etree
from spinneret.shadow import convert_userid_to_url


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
