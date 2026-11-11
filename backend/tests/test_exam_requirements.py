"""KAN-219: entrance tests come from a reviewed official document; unknown stays null."""
import copy
import json
import sys
from pathlib import Path

import pytest

from app.exam_requirements import DEFAULT_PATH, for_group, load, parse

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'scripts'))
import build_exam_requirements as builder  # noqa: E402

FIXTURE = Path(__file__).with_name('fixtures')/'exam-rules'/'sgu-2026-excerpt.txt'
SHA = '936121ed4c0454f562b3d7ca3c6979a339dadb140613486856b52c757bf26903'


def data():
    return json.loads(DEFAULT_PATH.read_bytes())


def encode(value):
    return json.dumps(value, ensure_ascii=False).encode()


def test_shipped_artifact_is_valid_and_matches_only_exact_groups():
    artifact = load()
    assert sorted(artifact.groups) == ['sgu-2026-4576', 'sgu-2026-4588']
    rules = for_group('sgu-2026-4588', year=2026, level='bachelor', code='09.03.04', study_form='full-time')
    assert [o.subject for t in rules.tests for o in t.options] == ['math', 'informatics', 'physics', 'russian']
    assert rules.source.sha256 == SHA
    for changed in (dict(year=2027), dict(code='09.03.01'), dict(study_form='part-time'), dict(level='specialist')):
        args = dict(year=2026, level='bachelor', code='09.03.04', study_form='full-time') | changed
        assert for_group('sgu-2026-4588', **args) is None
    assert for_group('unknown-group', year=2026, level='bachelor', code='09.03.04', study_form='full-time') is None


@pytest.mark.parametrize('mutate', [
    lambda d: d.update(format='exam-requirements-v0'),
    lambda d: d['groups'][0]['tests'][0]['options'][0].update(subject='astrology'),
    lambda d: d['groups'][0]['tests'][0]['options'][0].update(minScore=101),
    lambda d: d['groups'][0]['tests'][0]['options'][0].update(minScore='40'),
    lambda d: d['groups'][0]['tests'][1].update(position=3),
    lambda d: d['groups'][0]['tests'].append({'position': 4, 'options': [{'subject': 'math', 'minScore': 40}]}),
    lambda d: d['groups'][0].update(code='09.05.04'),
    lambda d: d['groups'][0].update(year=2025),
    lambda d: d['groups'][0].update(benefits=[]),
    lambda d: d['groups'][0].update(source='missing'),
    lambda d: d['groups'].append(copy.deepcopy(d['groups'][0])),
    lambda d: d['sources'][0].update(sha256='x'*64),
    lambda d: d['sources'][0].update(checkedAt='2026-11-11T09:40:00'),
    lambda d: d['sources'][0].update(url='javascript:alert(1)'),
    lambda d: d['groups'][0].pop('notes'),
])
def test_damaged_artifact_is_rejected_whole(mutate):
    value = data()
    mutate(value)
    with pytest.raises(ValueError):
        parse(encode(value))


def review():
    return builder.load_reviews()[0]


def text():
    return FIXTURE.read_text(encoding='utf-8')


def test_builder_is_reproducible_from_the_document_text():
    body = builder.build([review()], {SHA: text()})
    assert body == DEFAULT_PATH.read_bytes()
    assert builder.build([review()], {SHA: text()}) == body  # Idempotent import.
    parse(body)


@pytest.mark.parametrize(('mutate', 'message'), [
    (lambda r: r['groups'][0]['tests'][0]['options'][0].update(minScore=45), 'no evidence for math 45'),
    (lambda r: r['groups'][0]['tests'][1]['options'][1].update(minScore=41), 'physics is in conflict'),
    (lambda r: r['groups'][0]['tests'][2]['options'][0].update(minScore=None), 'no score and no recorded conflict'),
    (lambda r: r['groups'][0].update(anchor='09.03.04 Прикладная информатика'), 'group anchor'),
    (lambda r: r['groups'][0].update(code='09.03.01'), 'group anchor'),
    (lambda r: r['block'].update(end='99.99.99 Нет такого'), 'block end'),
    (lambda r: r['block']['evidence'].append('2. химия 40'), 'evidence not in block'),
    (lambda r: r['conflicts'][0]['evidence'].append('физика 39'), 'conflict evidence'),
])
def test_builder_refuses_facts_that_are_not_in_the_document(mutate, message):
    value = review()
    mutate(value)
    with pytest.raises(builder.ReviewError, match=message):
        builder.build([value], {SHA: text()})


def test_builder_requires_the_declared_document():
    with pytest.raises(builder.ReviewError, match='was not given'):
        builder.build([review()], {'0'*64: text()})
    other = review()
    other['groups'] = [dict(other['groups'][0])]
    with pytest.raises(builder.ReviewError, match='described twice'):
        builder.build([review(), dict(other, source=dict(other['source'], id='copy'))], {SHA: text()})


def test_conflict_note_reaches_every_group_that_uses_the_subject():
    groups = json.loads(builder.build([review()], {SHA: text()}))['groups']
    assert all(any('физике' in note for note in g['notes']) for g in groups)
