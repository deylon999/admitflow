"""Compatibility path for app.operations.migration_checks."""
import sys

from app.operations import migration_checks

sys.modules[__name__] = migration_checks
