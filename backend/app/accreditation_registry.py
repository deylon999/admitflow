"""Compatibility path for app.catalog.accreditation_registry."""
import sys

from app.catalog import accreditation_registry

sys.modules[__name__] = accreditation_registry
