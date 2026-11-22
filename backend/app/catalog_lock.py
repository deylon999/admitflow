"""Compatibility path for app.catalog.catalog_lock."""
import sys

from app.catalog import catalog_lock

sys.modules[__name__] = catalog_lock
