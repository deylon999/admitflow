"""Compatibility path for app.auth.account_dto."""
import sys

from app.auth import account_dto

sys.modules[__name__] = account_dto
