"""Compatibility path for app.catalog.university_names."""
import sys

from app.catalog import university_names

sys.modules[__name__] = university_names
