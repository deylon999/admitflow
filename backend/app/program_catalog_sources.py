"""Compatibility path for app.catalog.program_catalog_sources."""
import sys

from app.catalog import program_catalog_sources

sys.modules[__name__] = program_catalog_sources
