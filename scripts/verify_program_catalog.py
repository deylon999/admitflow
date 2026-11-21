"""Compatibility path for scripts.qa.verify_program_catalog."""

if __package__:
    from ._compat import forward
else:
    from _compat import forward

forward(__name__, "scripts.qa.verify_program_catalog")
