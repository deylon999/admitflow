"""Compatibility path for app.catalog.coverage."""
import sys

from app.catalog import coverage

sys.modules[__name__] = coverage
