"""Test cases for the __utils__ module."""
import pytest

from pandarus_remote.utils import log_exceptions


def test_log_exceptions(caplog) -> None:
    """Test that the exception is logged and raised again."""

    @log_exceptions
    def raise_exception():
        # pylint: disable=broad-exception-raised
        raise Exception("Test exception")

    with pytest.raises(Exception):
        raise_exception()
        assert "Test exception" in caplog.text
