"""Utility functions for the __pandarus_remote__ package."""
from pathlib import Path
from typing import Any, Callable, Dict, Tuple

from . import pr_app


def log_exceptions(func: Callable) -> Callable:
    """Log the exception and raise it again."""

    def wrapper(*args: Tuple[Any], **kwargs: Dict[str, Any]) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            pr_app.logger.exception(e)
            raise e

    return wrapper


def create_if_not_exists(path_func: Callable[[Any], Path]) -> Callable[[], Path]:
    """Decorator to create a directory if it doesn't exist."""

    def wrapper(instance: Any) -> Path:
        """Wrapper function for creating a directory if it doesn't exist."""
        path = path_func(instance)
        path.mkdir(parents=True, exist_ok=True)
        return path

    return wrapper
