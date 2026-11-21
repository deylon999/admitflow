"""Compatibility path for app.catalog.source_catalog."""
import sys

from app.catalog import source_catalog

sys.modules[__name__] = source_catalog
