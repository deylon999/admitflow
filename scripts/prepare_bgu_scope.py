"""Compatibility path for scripts.data.prepare_bgu_scope."""

if __package__:
    from ._compat import forward
else:
    from _compat import forward

forward(__name__, "scripts.data.prepare_bgu_scope")
