"""Compatibility path for app.catalog.program_catalog_batch."""
import sys

from app.catalog import program_catalog_batch

if __name__ == '__main__':
    raise SystemExit(program_catalog_batch.main())
else:
    sys.modules[__name__] = program_catalog_batch
