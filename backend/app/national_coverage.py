"""Compatibility path for app.catalog.national_coverage."""
import sys

from app.catalog import national_coverage

if __name__ == '__main__':
    raise SystemExit(national_coverage.main())
else:
    sys.modules[__name__] = national_coverage
