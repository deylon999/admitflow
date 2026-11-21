"""Compatibility path for scripts.data.group_source_formats."""

if __package__:
    from ._compat import forward
else:
    from _compat import forward

forward(__name__, "scripts.data.group_source_formats")
