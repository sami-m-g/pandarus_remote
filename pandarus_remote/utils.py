"""Utility functions for the __pandarus_remote__ package."""
import logging
import os
from functools import wraps
from http import HTTPStatus
from pathlib import Path
from typing import Any, Callable, Dict, Tuple

from flask import Response, send_file, url_for

from .errors import (
    IntersectionWithSelfError,
    InvalidIntersectionFileTypesError,
    InvalidIntersectionGeometryTypeError,
    InvalidRasterstatsFileTypesError,
    NoEntryFoundError,
    ResultAlreadyExistsError,
)


def loggable(func: Callable) -> Callable:
    """Decorator for adding logs to functions."""

    @wraps(func)
    def wrapper(*args: Tuple[Any], **kwargs: Dict[str, Any]) -> Any:
        """Wrapper function for adding logs to functions."""
        if args or kwargs:
            arguments = ", ".join(
                [repr(arg) for arg in args] + [repr(value) for value in kwargs.values()]
            )
            arguments_str = f"arguments: {arguments}"
        else:
            arguments_str = "no arguments"
        logging.debug("Starting %s with %s.", func.__name__, arguments_str)
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            logging.exception(e)
            raise e
        results_str = f"return: {result}" if result else "no return"
        logging.debug("Finished %s with %s.", func.__name__, results_str)
        return result

    return wrapper


def create_if_not_exists(
    path_function: Callable[[Tuple[Any], Dict[str, Any]], Path]
) -> Callable[[], Path]:
    """Decorator to create a directory if it doesn't exist."""

    @wraps(path_function)
    def wrapper(*args: Tuple[Any], **kwargs: Dict[str, Any]) -> Path:
        """Wrapper function for creating a directory if it doesn't exist."""
        path = path_function(*args, **kwargs)
        path.mkdir(parents=True, exist_ok=True)
        return path

    return wrapper


def get_calculation_endpoint(
    calculation_function: Callable[[], str]
) -> Callable[[], Response]:
    """Decorator for get_calculation endpoints."""

    @wraps(calculation_function)
    def wrapper() -> Path:
        """Wrapper function for get_calculation endpoints."""
        try:
            result = calculation_function()
            return (
                send_file(
                    result,
                    mimetype="application/octet-stream",
                    as_attachment=True,
                    download_name=os.path.basename(result),
                ),
                HTTPStatus.OK,
            )
        except NoEntryFoundError as nefe:
            return {"error": str(nefe)}, HTTPStatus.NOT_FOUND
        except ResultAlreadyExistsError as raee:
            return {"error": str(raee)}, HTTPStatus.CONFLICT

    return wrapper


def calculate_endpoint(
    calculation_function: Callable[[], str]
) -> Callable[[], Response]:
    """Decorator for calculate endpoints."""

    @wraps(calculation_function)
    def wrapper() -> Response:
        """Wrapper function for calculate endpoints."""
        try:
            job_id = calculation_function()
            return (
                url_for("routes_blueprint.status", job_id=job_id),
                HTTPStatus.ACCEPTED,
            )
        except NoEntryFoundError as nefe:
            return {"error": str(nefe)}, HTTPStatus.NOT_FOUND
        except ResultAlreadyExistsError as raee:
            return {"error": str(raee)}, HTTPStatus.CONFLICT
        except InvalidRasterstatsFileTypesError as irfte:
            return {"error": str(irfte)}, HTTPStatus.BAD_REQUEST
        except InvalidIntersectionGeometryTypeError as iigte:
            return {"error": str(iigte)}, HTTPStatus.BAD_REQUEST
        except InvalidIntersectionFileTypesError as iifte:
            return {"error": str(iifte)}, HTTPStatus.BAD_REQUEST
        except IntersectionWithSelfError as iwse:
            return {"error": str(iwse)}, HTTPStatus.BAD_REQUEST

    return wrapper
