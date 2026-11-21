"""Compatibility path for app.auth.account_api, including patches to globals."""
import sys

from .auth import account_api

sys.modules[__name__] = account_api
