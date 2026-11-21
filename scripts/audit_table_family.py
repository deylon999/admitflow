#!/usr/bin/env python3
"""Compatibility path for scripts.data.audit_table_family."""

if __package__:
    from ._compat import forward
else:
    from _compat import forward

forward(__name__, "scripts.data.audit_table_family")
