"""Compatibility path for scripts.ops.postgres_runtime."""

if __package__:
    from ._compat import forward
else:
    from _compat import forward

forward(__name__, "scripts.ops.postgres_runtime")
