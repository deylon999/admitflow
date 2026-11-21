"""Compatibility path for scripts.data.review_section_family."""

if __package__:
    from ._compat import forward
else:
    from _compat import forward

forward(__name__, "scripts.data.review_section_family")
