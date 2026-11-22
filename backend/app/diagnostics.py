"""Compatibility path for app.operations.diagnostics."""
import sys

from app.operations import diagnostics

if __name__ == '__main__':
    raise SystemExit(diagnostics.main())
else:
    sys.modules[__name__] = diagnostics
