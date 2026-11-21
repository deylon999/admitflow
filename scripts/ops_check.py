#!/usr/bin/env python3
"""Compatibility path for scripts.ops.ops_check."""

if __package__:
    from ._compat import forward
else:
    from _compat import forward

forward(__name__, "scripts.ops.ops_check")
