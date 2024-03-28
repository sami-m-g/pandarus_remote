"""Test cases for the __app__ module."""

from pandarus_remote.app import create_app
from pandarus_remote.version import __version__


def test_create_app(caplog) -> None:
    """Test that the create_app is created."""
    caplog.set_level("DEBUG")

    create_app(
        {"TESTING": True, "DEBUG": True, "MAX_CONTENT_LENGTH": 250 * 1024 * 1024}
    )
    assert f"Starting pandarus_remote service version {__version__}" in caplog.text
