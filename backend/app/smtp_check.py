"""Compatibility path for app.operations.smtp_check."""
import sys

from app.operations import smtp_check

if __name__ == '__main__':
    raise SystemExit(smtp_check.main())
else:
    sys.modules[__name__] = smtp_check
