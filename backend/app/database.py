"""Compatibility path for app.watchlist.models and the shared database registry."""
import sys

from .watchlist import models

sys.modules[__name__] = models
