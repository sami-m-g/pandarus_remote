"""__pandarus_remote__ web service package."""
__all__ = ["__version__", "pr_app"]

from flask import Flask

from .version import __version__

pr_app = Flask(__name__)
