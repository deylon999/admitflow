"""Compatibility path for app.watchlist.changes."""
import sys

from app.watchlist import changes

sys.modules[__name__] = changes
