"""Compatibility path for app.catalog.program_catalog_review."""
import sys

from app.catalog import program_catalog_review

sys.modules[__name__] = program_catalog_review
