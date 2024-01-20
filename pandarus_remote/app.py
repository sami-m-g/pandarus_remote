"""Main entry point for the __pandarus_remote__ service."""
from typing import Any, Dict, Optional

from flask import Flask
from pandarus import __version__ as pandarus_version

from . import __version__, pr_app
from .routes import routes_blueprint


def webapp(configs: Optional[Dict[str, Any]]) -> Flask:
    """Create the flask app."""
    if not configs:
        configs = {"MAX_CONTENT_LENGTH": 250 * 1024 * 1024}  # pragma: no cover

    pr_app.register_blueprint(routes_blueprint)
    pr_app.config.update(configs)
    pr_app.logger.info(
        "Starting %s service version %s using pandaris versions %s.",
        pr_app.name,
        __version__,
        pandarus_version,
    )
    pr_app.logger.debug("App configs: %s", configs)

    return pr_app
