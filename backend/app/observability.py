"""Compatibility path for app.operations.observability."""
import sys

from app.operations import observability

if __name__ == '__main__':
    raise SystemExit(observability.main())
else:
    sys.modules[__name__] = observability
