"""Test cases for the __utils__ module."""
from pandarus_remote.app import webapp
from pandarus_remote.version import __version__


def test_webapp(caplog) -> None:
    """Test that the webapp is created."""
    webapp({"TESTING": True, "DEBUG": True, "MAX_CONTENT_LENGTH": 250 * 1024 * 1024})
    assert f"Starting pandarus_remote service version {__version__}" in caplog.text
