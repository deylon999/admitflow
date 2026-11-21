#!/usr/bin/env python3
"""Compatibility path for scripts.qa.replay_archives."""

if __package__:
    from ._compat import forward
else:
    from _compat import forward

forward(__name__, "scripts.qa.replay_archives")
