"""Compatibility path for app.auth.account_limits."""
import sys

from app.auth import account_limits

sys.modules[__name__] = account_limits
