"""Compatibility path for scripts.reports.weekly_report."""

if __package__:
    from ._compat import forward
else:
    from _compat import forward

forward(__name__, "scripts.reports.weekly_report")
