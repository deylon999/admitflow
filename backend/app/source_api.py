"""Compatibility path for app.watchlist.source_api."""
import sys

from app.watchlist import source_api

sys.modules[__name__] = source_api
