"""Compatibility path for app.watchlist.direction_budget."""
import sys

from app.watchlist import direction_budget

sys.modules[__name__] = direction_budget
