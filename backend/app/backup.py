"""Compatibility path for app.operations.backup."""
import sys

from app.operations import backup

if __name__ == '__main__':
    raise SystemExit(backup.main())
else:
    sys.modules[__name__] = backup
