"""Compatibility path for app.competitions.competition_api."""
import sys

from app.competitions import competition_api

sys.modules[__name__] = competition_api
