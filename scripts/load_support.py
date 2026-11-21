"""Compatibility path for scripts.qa.load_support."""

if __package__:
    from ._compat import forward
else:
    from _compat import forward

forward(__name__, "scripts.qa.load_support")
