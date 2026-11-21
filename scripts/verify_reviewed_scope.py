"""Compatibility path for scripts.qa.verify_reviewed_scope."""

if __package__:
    from ._compat import forward
else:
    from _compat import forward

forward(__name__, "scripts.qa.verify_reviewed_scope")
