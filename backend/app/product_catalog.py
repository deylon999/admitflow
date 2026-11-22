"""Compatibility path for app.catalog.product_catalog."""
import sys

from app.catalog import product_catalog

sys.modules[__name__] = product_catalog
