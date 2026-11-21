"""Compatibility path for scripts.qa.check_doc_links."""

if __package__:
    from ._compat import forward
else:
    from _compat import forward

forward(__name__, "scripts.qa.check_doc_links")
