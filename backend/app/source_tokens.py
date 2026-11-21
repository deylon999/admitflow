"""Compatibility path for app.watchlist.source_tokens."""
import sys

from app.watchlist import source_tokens

sys.modules[__name__] = source_tokens
