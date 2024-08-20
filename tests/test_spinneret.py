"""For testing the spinneret module."""

from src.spinneret.spinneret import hello_world


def test_test():
    """Test test"""
    assert 1 == 1


def test_hello_world():
    """Test hello_world"""
    assert hello_world("Hello world", False) == "Hello world"
