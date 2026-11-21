"""Compatibility path for app.catalog.program_catalog_batch_fetch."""
import sys

from app.catalog import program_catalog_batch_fetch

sys.modules[__name__] = program_catalog_batch_fetch
