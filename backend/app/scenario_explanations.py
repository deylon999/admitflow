"""Compatibility path for app.competitions.scenario_explanations."""
import sys

from app.competitions import scenario_explanations

sys.modules[__name__] = scenario_explanations
