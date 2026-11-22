"""Compatibility path for app.operations.maintenance."""
import sys

from app.operations import maintenance

if __name__ == '__main__':
    maintenance.main()
else:
    sys.modules[__name__] = maintenance
