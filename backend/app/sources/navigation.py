"""Admission-navigation ranking, never source eligibility or format attestation."""
import re
from urllib.parse import urlsplit

EXCLUDED=re.compile(r'/news/|/novost|/vacanc|/press/|/smi/|/ads/|замещени|при[её]м на работу|конкурс науч|конкурс работ|трудоустройств',re.I)
LIST_LABEL=re.compile(r'конкурсн.{0,12}списк|рейтингов.{0,12}списк|ранжирован.{0,12}списк|списк.{0,35}(поступ|подавш|поданн|абитур)|конкурсн.{0,8}ситуаци',re.I)
ADMISSION_LABEL=re.compile(r'абитуриент|поступающ|при[её]мная комисс|при[её]м.{0,8}202[5-9]',re.I)
ADMISSION_SCOPE=re.compile(r'(^|[./_-])(admission|abitur\w*|abit|priem|postup\w*)([./_-]|$)',re.I)
LIST_PATH=re.compile(r'(^|[/_-])(rating|rank\w*|spisk\w*|competitive|konkurs\w*)([/_.?-]|$)',re.I)


def admissions_link_score(url,label):
    label=' '.join(label.split());parts=urlsplit(url)
    context=label+' '+parts.path
    if EXCLUDED.search(context):return 0
    if LIST_LABEL.search(label):return 100
    admission_path=ADMISSION_SCOPE.search((parts.hostname or '')+parts.path)
    if admission_path and LIST_PATH.search(parts.path):return 90
    if ADMISSION_LABEL.search(label):return 60
    if admission_path:return 40
    return 0
