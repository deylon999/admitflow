#!/usr/bin/env python3
"""Compatibility path for scripts.data.sanitize_pilot."""

if __package__:
    from ._compat import forward
else:
    from _compat import forward

forward(__name__, "scripts.data.sanitize_pilot")
