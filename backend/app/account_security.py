"""Compatibility path sharing credential helpers and their module state."""
import sys

from .auth import account_security

sys.modules[__name__] = account_security
