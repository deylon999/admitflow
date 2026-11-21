"""Compatibility path for app.watchlist.importing."""
import sys

from app.watchlist import importing

sys.modules[__name__] = importing
