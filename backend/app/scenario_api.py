"""Compatibility path for app.competitions.scenario_api."""
import sys

from app.competitions import scenario_api

sys.modules[__name__] = scenario_api
