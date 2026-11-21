"""Compatibility path for app.catalog.catalog_import."""
import sys

from app.catalog import catalog_import

if __name__ == '__main__':
    catalog_import.main()
else:
    sys.modules[__name__] = catalog_import
