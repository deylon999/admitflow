"""Compatibility path for scripts.data.pack_profiles."""

if __package__:
    from ._compat import forward
else:
    from _compat import forward

forward(__name__, "scripts.data.pack_profiles")
