"""Compatibility path for app.catalog.exam_requirements."""
import sys

from app.catalog import exam_requirements

sys.modules[__name__] = exam_requirements
