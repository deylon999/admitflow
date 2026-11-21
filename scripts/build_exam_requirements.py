"""Compatibility path for scripts.data.build_exam_requirements."""

if __package__:
    from ._compat import forward
else:
    from _compat import forward

forward(__name__, "scripts.data.build_exam_requirements")
