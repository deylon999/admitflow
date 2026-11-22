"""Compatibility path for app.catalog.product_catalog_schemas."""
import sys

from app.catalog import product_catalog_schemas

sys.modules[__name__] = product_catalog_schemas
