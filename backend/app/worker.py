"""Compatibility path for app.operations.worker."""
import sys

from app.operations import worker

if __name__ == '__main__':
    worker.limit_memory()
    raise SystemExit(worker.main())
else:
    sys.modules[__name__] = worker
