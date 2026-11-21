"""Compatibility path for app.watchlist.source_history."""
import sys

from app.watchlist import source_history

sys.modules[__name__] = source_history
