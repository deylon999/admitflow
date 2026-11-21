"""Compatibility path for app.operations.jobs."""
import sys

from app.operations import jobs

sys.modules[__name__] = jobs
