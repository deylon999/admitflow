"""Compatibility path for app.sources.source_operations."""
import sys

from app.sources import source_operations

sys.modules[__name__] = source_operations
