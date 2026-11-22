"""Compatibility path for app.operations.migrations."""
import sys

from app.operations import migrations

sys.modules[__name__] = migrations
