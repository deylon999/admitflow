"""Compatibility path for app.core.config."""
import sys

from app.core import config

sys.modules[__name__] = config
