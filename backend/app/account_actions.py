"""Compatibility path for app.auth.account_actions."""
import sys

from app.auth import account_actions

sys.modules[__name__] = account_actions
