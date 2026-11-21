"""Compatibility path for app.core.schema_base."""
import sys

from app.core import schema_base

sys.modules[__name__] = schema_base
