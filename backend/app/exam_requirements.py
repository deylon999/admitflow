"""Reviewed entrance test requirements per competition group (KAN-219).

The artifact backend/app/data/exam-requirements.json is written by
scripts/build_exam_requirements.py from a university's official document and a
review file; every declared fact is checked against the document text before
it lands here. A requirement set is shown only for a group whose year, level,
code and study form match exactly. Unknown parts stay null: a minimum score
the document states inconsistently is null with a note, never a guess.
"""
from dataclasses import dataclass
from datetime import date, datetime
from functools import lru_cache
import hashlib
import json
import logging
from pathlib import Path
import re

from .national_catalog import clean_text, valid_url

DEFAULT_PATH = Path(__file__).with_name('data')/'exam-requirements.json'
FORMAT = 'exam-requirements-v1'
SUBJECTS = {
    'russian': 'Русский язык', 'math': 'Математика (профильная)', 'physics': 'Физика', 'informatics': 'Информатика',
    'chemistry': 'Химия', 'biology': 'Биология', 'history': 'История', 'geography': 'География',
    'social': 'Обществознание', 'literature': 'Литература', 'foreign': 'Иностранный язык',
}
LEVELS = ('bachelor', 'specialist')
FORMS = ('full-time', 'part-time', 'extramural')
CODE = re.compile(r'\d{2}\.0[35]\.\d{2}')
log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Option:
    subject: str
    min_score: int | None


@dataclass(frozen=True)
class Test:
    position: int
    options: tuple[Option, ...]


@dataclass(frozen=True)
class Source:
    id: str
    university_id: str
    title: str
    url: str
    document_date: date
    sha256: str
    pages: tuple[int, ...]
    checked_at: datetime
    cross_check_url: str | None
    cross_check_note: str | None


@dataclass(frozen=True)
class GroupRules:
    group_id: str
    year: int
    level: str
    code: str
    study_form: str
    source: Source
    tests: tuple[Test, ...]
    additional_tests: tuple[Test, ...] | None
    notes: tuple[str, ...]


@dataclass(frozen=True)
class Artifact:
    groups: dict
    sha256: str


def _int(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError('invalid number')
    return value


def _tests(items, *, allow_empty):
    if not isinstance(items, list) or (not items and not allow_empty) or len(items) > 8:
        raise ValueError('invalid tests')
    tests = []
    for expected, item in enumerate(items, 1):
        if set(item) != {'position', 'options'} or item['position'] != expected:
            raise ValueError('tests must be numbered 1..N')
        options = item['options']
        if not isinstance(options, list) or not 1 <= len(options) <= 6:
            raise ValueError('invalid options')
        parsed = []
        for option in options:
            if set(option) != {'subject', 'minScore'} or option['subject'] not in SUBJECTS:
                raise ValueError('unknown subject')
            score = option['minScore']
            parsed.append(Option(option['subject'], None if score is None else _int(score, 1, 100)))
        if len({o.subject for o in parsed}) != len(parsed):
            raise ValueError('duplicate subject in one test')
        tests.append(Test(expected, tuple(parsed)))
    subjects = [o.subject for t in tests for o in t.options]
    if len(subjects) != len(set(subjects)):
        raise ValueError('a subject appears in two tests')
    return tuple(tests)


def parse(body):
    if not isinstance(body, bytes) or not 1 <= len(body) <= 2*1024*1024:
        raise ValueError('invalid exam requirements size')
    try:
        data = json.loads(body.decode('utf-8'))
        if set(data) != {'format', 'sources', 'groups'} or data['format'] != FORMAT:
            raise ValueError('unsupported exam requirements')
        sources = {}
        for row in data['sources']:
            cross = row['crossCheck']
            source = Source(
                id=clean_text(row['id'], 80), university_id=clean_text(row['universityId'], 80), title=clean_text(row['title'], 400),
                url=valid_url(row['url']), document_date=date.fromisoformat(row['documentDate']), sha256=row['sha256'],
                pages=tuple(_int(p, 1, 2000) for p in row['pages']), checked_at=datetime.fromisoformat(row['checkedAt']),
                cross_check_url=None if cross is None else valid_url(cross['url']),
                cross_check_note=None if cross is None else clean_text(cross['note'], 600))
            if (source.id in sources or not re.fullmatch(r'[a-f0-9]{64}', source.sha256) or not source.pages
                    or source.checked_at.tzinfo is None or source.checked_at.date() < source.document_date):
                raise ValueError('invalid source')
            sources[source.id] = source
        groups = {}
        for row in data['groups']:
            source = sources[row['source']]
            additional = row['additionalTests']
            rules = GroupRules(
                group_id=clean_text(row['groupId'], 36), year=_int(row['year'], 2020, 2100), level=row['level'], code=row['code'],
                study_form=row['studyForm'], source=source, tests=_tests(row['tests'], allow_empty=False),
                additional_tests=None if additional is None else _tests(additional, allow_empty=True),
                notes=tuple(clean_text(n, 600) for n in row['notes']))
            if (rules.group_id in groups or rules.level not in LEVELS or rules.study_form not in FORMS
                    or not CODE.fullmatch(rules.code) or (rules.code[3:5] == '05') != (rules.level == 'specialist')
                    or rules.year != source.document_date.year or row['benefits'] is not None):
                raise ValueError('invalid group rules')
            groups[rules.group_id] = rules
        return Artifact(groups, hashlib.sha256(body).hexdigest())
    except (KeyError, TypeError, AttributeError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError('invalid exam requirements') from error


@lru_cache(maxsize=1)
def load():
    return parse(DEFAULT_PATH.read_bytes())


def for_group(group_id, *, year, level, code, study_form, artifact=None):
    """Reviewed rules for this exact group, or None when unknown or not matching."""
    artifact = artifact or load()
    rules = artifact.groups.get(group_id)
    if rules is None:
        return None
    if (rules.year, rules.level, rules.code, rules.study_form) != (year, level, code, study_form):
        # A rule written for another year, code or form is never shown for this group.
        log.warning('exam_requirements_mismatch', extra={'groupId': group_id})
        return None
    return rules
