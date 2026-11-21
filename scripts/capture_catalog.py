"""Compatibility path for scripts.data.capture_catalog."""

if __package__:
    from ._compat import forward
else:
    from _compat import forward

forward(__name__, "scripts.data.capture_catalog")
