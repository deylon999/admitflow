"""Compatibility path for scripts.data.admissions_inventory."""

if __package__:
    from ._compat import forward
else:
    from _compat import forward

forward(__name__, "scripts.data.admissions_inventory")
