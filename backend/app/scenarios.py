"""Compatibility path for app.competitions.scenarios."""
import sys

from app.competitions import scenarios

sys.modules[__name__] = scenarios
