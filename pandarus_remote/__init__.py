"""__pandarus_remote__ web service package."""
__all__ = ["__version__", "create_app"]

from .app import create_app
from .version import __version__
