"""Compatibility path for app.catalog.university_name_report."""
import sys

from app.catalog import university_name_report

if __name__ == '__main__':
    university_name_report.main()
else:
    sys.modules[__name__] = university_name_report
