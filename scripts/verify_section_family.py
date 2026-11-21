"""Compatibility path for scripts.qa.verify_section_family."""

if __package__:
    from ._compat import forward
else:
    from _compat import forward

forward(__name__, "scripts.qa.verify_section_family")
