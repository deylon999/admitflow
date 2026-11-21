#!/usr/bin/env python3
"""Compatibility path for scripts.qa.load_server."""

if __package__:
    from ._compat import forward
else:
    from _compat import forward

forward(__name__, "scripts.qa.load_server")
