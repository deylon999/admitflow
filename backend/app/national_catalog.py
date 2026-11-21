"""Compatibility path for app.catalog.national_catalog."""
import sys

from app.catalog import national_catalog

if __name__ == '__main__':
    national_catalog.main()
else:
    sys.modules[__name__] = national_catalog
