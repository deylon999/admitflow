"""Compatibility path for scripts.data.source_inventory."""

if __package__:
    from ._compat import forward
else:
    from _compat import forward

forward(__name__, "scripts.data.source_inventory")
