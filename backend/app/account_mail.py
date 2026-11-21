"""Compatibility path sharing the SMTP transport and its module state."""
import sys

from .auth import account_mail

sys.modules[__name__] = account_mail
