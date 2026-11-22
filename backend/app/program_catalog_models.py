"""Compatibility path for app.catalog.program_catalog_models."""
import sys

from app.catalog import program_catalog_models

sys.modules[__name__] = program_catalog_models
