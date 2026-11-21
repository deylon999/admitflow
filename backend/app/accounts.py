"""Compatibility path for the single set of ORM classes in app.auth.accounts."""
import sys

from .auth import accounts

sys.modules[__name__] = accounts
