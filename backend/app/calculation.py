"""Compatibility path for app.competitions.calculation."""
import sys

from app.competitions import calculation

sys.modules[__name__] = calculation
