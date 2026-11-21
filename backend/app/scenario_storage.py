"""Compatibility path for app.competitions.scenario_storage."""
import sys

from app.competitions import scenario_storage

sys.modules[__name__] = scenario_storage
