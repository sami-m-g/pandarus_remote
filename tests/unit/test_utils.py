"""Test cases for the __utils__ module."""

from http import HTTPStatus
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pytest

from pandarus_remote.errors import (
    IntersectionWithSelfError,
    InvalidIntersectionFileTypesError,
    InvalidIntersectionGeometryTypeError,
    InvalidRasterstatsFileTypesError,
    NoEntryFoundError,
    ResultAlreadyExistsError,
)
from pandarus_remote.utils import (
    calculate_endpoint,
    create_if_not_exists,
    get_calculation_endpoint,
    loggable,
)


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


def test_create_if_not_exists(tmp_path) -> None:
    """Test the create_if_not_exists decorator."""

    @create_if_not_exists
    def _path_function() -> Path:
        return tmp_path.joinpath("test")

    path = _path_function()
    assert path.exists()


def test_get_calculation_endpoint(monkeypatch) -> None:
    """Test the get_calculation_endpoint decorator."""
    monkeypatch.setattr("pandarus_remote.utils.send_file", lambda *_, **__: "test")

    @get_calculation_endpoint
    def _calculation_function() -> str:
        return "test"

    assert _calculation_function() == ("test", HTTPStatus.OK)


def test_get_calculation_endpoint_no_entry_found(monkeypatch) -> None:
    """Test the get_calculation_endpoint decorator with NoEntryFoundError."""
    monkeypatch.setattr("pandarus_remote.utils.send_file", lambda *_, **__: "test")

    error = NoEntryFoundError("Test")

    @get_calculation_endpoint
    def _calculation_function() -> str:
        raise error

    assert _calculation_function() == ({"error": str(error)}, HTTPStatus.NOT_FOUND)


def test_get_calculation_endpoint_result_already_exists(monkeypatch) -> None:
    """Test the get_calculation_endpoint decorator with ResultAlreadyExistsError."""
    monkeypatch.setattr("pandarus_remote.utils.send_file", lambda *_, **__: "test")

    error = ResultAlreadyExistsError("Test")

    @get_calculation_endpoint
    def _calculation_function() -> str:
        raise error

    assert _calculation_function() == ({"error": str(error)}, HTTPStatus.CONFLICT)


def test_calculate_endpoint(monkeypatch) -> None:
    """Test the calculate_endpoint decorator."""
    monkeypatch.setattr("pandarus_remote.utils.url_for", lambda *_, **__: "test")

    @calculate_endpoint
    def _calculation_function() -> str:
        return "test"

    assert _calculation_function() == ("test", HTTPStatus.ACCEPTED)


def test_calculate_endpoint_no_entry_found(monkeypatch) -> None:
    """Test the test_calculate_endpoint decorator with NoEntryFoundError."""
    monkeypatch.setattr("pandarus_remote.utils.send_file", lambda *_, **__: "test")

    error = NoEntryFoundError("Test")

    @calculate_endpoint
    def _calculation_function() -> str:
        raise error

    assert _calculation_function() == ({"error": str(error)}, HTTPStatus.NOT_FOUND)


def test_calculate_endpoint_result_already_exists(monkeypatch) -> None:
    """Test the test_calculate_endpoint decorator with ResultAlreadyExistsError."""
    monkeypatch.setattr("pandarus_remote.utils.send_file", lambda *_, **__: "test")

    error = ResultAlreadyExistsError("Test")

    @calculate_endpoint
    def _calculation_function() -> str:
        raise error

    assert _calculation_function() == ({"error": str(error)}, HTTPStatus.CONFLICT)


def test_calculate_endpoint_invalid_rasterstats_file_types(monkeypatch) -> None:
    """Test the test_calculate_endpoint decorator with
    InvalidRasterstatsFileTypesError."""
    monkeypatch.setattr("pandarus_remote.utils.send_file", lambda *_, **__: "test")

    error = InvalidRasterstatsFileTypesError("sha2561", "raster", "sha2562", "vector")

    @calculate_endpoint
    def _calculation_function() -> str:
        raise error

    assert _calculation_function() == ({"error": str(error)}, HTTPStatus.BAD_REQUEST)


def test_calculate_endpoint_invalid_intersection_geometry_type(monkeypatch) -> None:
    """Test the test_calculate_endpoint decorator with
    InvalidIntersectionGeometryTypeError."""
    monkeypatch.setattr("pandarus_remote.utils.send_file", lambda *_, **__: "test")

    error = InvalidIntersectionGeometryTypeError(
        "sha2561", "raster", "sha2562", "vector"
    )

    @calculate_endpoint
    def _calculation_function() -> str:
        raise error

    assert _calculation_function() == ({"error": str(error)}, HTTPStatus.BAD_REQUEST)


def test_calculate_endpoint_invalid_intersection_file_types(monkeypatch) -> None:
    """Test the test_calculate_endpoint decorator with
    InvalidIntersectionFileTypesError."""
    monkeypatch.setattr("pandarus_remote.utils.send_file", lambda *_, **__: "test")

    error = InvalidIntersectionFileTypesError("sha2561", "raster", "sha2562", "vector")

    @calculate_endpoint
    def _calculation_function() -> str:
        raise error

    assert _calculation_function() == ({"error": str(error)}, HTTPStatus.BAD_REQUEST)


def test_calculate_endpoint_intersection_with_self(monkeypatch) -> None:
    """Test the test_calculate_endpoint decorator with IntersectionWithSelfError."""
    monkeypatch.setattr("pandarus_remote.utils.send_file", lambda *_, **__: "test")

    error = IntersectionWithSelfError("sha2561")

    @calculate_endpoint
    def _calculation_function() -> str:
        raise error

    assert _calculation_function() == ({"error": str(error)}, HTTPStatus.BAD_REQUEST)
