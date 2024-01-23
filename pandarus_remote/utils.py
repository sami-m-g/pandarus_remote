"""Utility functions for the __pandarus_remote__ package."""
import logging
from pathlib import Path
from typing import Any, Callable, Dict, Tuple


def loggable(func: Callable) -> Callable:
    """Decorator for adding logs to functions."""

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


def create_if_not_exists(path_func: Callable[[Any], Path]) -> Callable[[], Path]:
    """Decorator to create a directory if it doesn't exist."""

    def wrapper(instance: Any) -> Path:
        """Wrapper function for creating a directory if it doesn't exist."""
        path = path_func(instance)
        path.mkdir(parents=True, exist_ok=True)
        return path

    return wrapper
