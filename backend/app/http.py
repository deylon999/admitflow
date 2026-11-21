"""Compatibility path for app.core.http."""
import sys

from app.core import http

sys.modules[__name__] = http
