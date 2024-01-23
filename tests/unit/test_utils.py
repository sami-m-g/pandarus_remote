"""Test cases for the __utils__ module."""
from typing import Any, Dict, Optional, Tuple

import pytest

from pandarus_remote.utils import loggable


def test_loggable_with_arguments_and_return(caplog) -> None:
    """Test the loggable decorator with arguments and return."""
    caplog.set_level("DEBUG")

    @loggable
    def _return_function(arg1: str, arg2: Optional[Dict] = None) -> Tuple[str, Dict]:
        return arg1, arg2

    arg_str, arg_dict = "Test", {"test": "test"}
    ret1, ret2 = _return_function("Test", arg2={"test": "test"})
    assert ret1 == arg_str
    assert ret2 == arg_dict
    assert (
        "Starting _return_function with arguments: 'Test', {'test': 'test'}."
        in caplog.text
    )
    assert (
        "Finished _return_function with return: ('Test', {'test': 'test'})."
        in caplog.text
    )


def test_loggable_without_arguments_or_return(caplog) -> None:
    """Test the loggable decorator without arguments or return."""
    caplog.set_level("DEBUG")

    @loggable
    def _no_return_function() -> None:
        pass

    _no_return_function()
    assert "Starting _no_return_function with no arguments." in caplog.text
    assert "Finished _no_return_function with no return." in caplog.text


def test_loggable_with_exception(caplog) -> None:
    """Test the loggable decorator with exception."""
    caplog.set_level("DEBUG")

    @loggable
    def _exception_function(*_: Tuple[Any], **__: Dict[str, Any]) -> None:
        # pylint: disable=broad-exception-raised
        raise Exception("Test")

    with pytest.raises(Exception):
        _exception_function()
    assert "Starting _exception_function with no arguments." in caplog.text
    assert "Exception: Test" in caplog.text
