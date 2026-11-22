"""Compatibility path for app.catalog.catalog_identity."""
import sys

from app.catalog import catalog_identity

sys.modules[__name__] = catalog_identity
