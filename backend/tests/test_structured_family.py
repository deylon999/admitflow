"""KAN-220: JSON and CSV lists use the same adapter interface, worker and safety rules as HTML."""
import hashlib
import json
from dataclasses import replace

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.admissions import CandidateEntry, PublishedSnapshot, SourceSnapshot
from app.jobs import SourceJob, clock, enqueue, enqueue_all
from app.sources.contracts import AdapterError, SourceBinding
from app.sources.fetcher import FetchResult
from app.sources.registry import Attestation, Registry
from app.sources.storage import RawStore
from app.sources.structured_family import CSV_VERSION, JSON_VERSION, StructuredProfile, make_structured_adapter, parse_structured
from app.worker import run_once
from native_support import postgres_engine  # noqa: F401
from source_helpers import NOW, seed_source

SECRET = b'k'*32
JSON_URL = 'https://example.org/list.json'
CSV_URL = 'https://example.org/list.csv'


def records(count=4):
    return [dict(n=i, id=f'A-{i:03}', ball=300 - i, agree='да' if i % 2 else 'нет', prio=1 if i < 3 else None, state='' if i != 4 else 'Зачислен') for i in range(1, count + 1)]


def json_body(items=None):
    return json.dumps({'data': {'items': records() if items is None else items}}, ensure_ascii=False).encode()


def csv_body(items=None, delimiter=';'):
    lines = [delimiter.join(['№', 'Код', 'Баллы', 'Согласие', 'Приоритет', 'Статус'])]
    for r in records() if items is None else items:
        lines.append(delimiter.join([str(r['n']), r['id'], str(r['ball']).replace('.', ','), r['agree'], '' if r['prio'] is None else str(r['prio']), r['state']]))
    return ('\n'.join(lines) + '\n').encode('cp1251')


FIELDS_JSON = (('rank', 'n'), ('code', 'id'), ('score', 'ball'), ('consent', 'agree'), ('priority', 'prio'), ('status', 'state'))
FIELDS_CSV = (('rank', '№'), ('code', 'Код'), ('score', 'Баллы'), ('consent', 'Согласие'), ('priority', 'Приоритет'), ('status', 'Статус'))


def response(url, body, charset='utf-8'):
    return FetchResult(url, body, 'application/json' if url.endswith('json') else 'text/csv', hashlib.sha256(body).hexdigest(), NOW, charset)


def profile(version, url, **changes):
    base = dict(source_id='source-1', group_id='group-1', url=url, year=2026, rows=4, seats=10, version=version)
    if version == JSON_VERSION:
        base.update(fields=FIELDS_JSON, items_path=('data', 'items'))
    else:
        base.update(fields=FIELDS_CSV, headers=('№', 'Код', 'Баллы', 'Согласие', 'Приоритет', 'Статус'))
    return StructuredProfile(**(base | changes))


def binding(url, version):
    return SourceBinding('source-1', 'group-1', 2026, url, 'example.org', version, 'archive', True)


def proof(version, url, body):
    digest = hashlib.sha256(body).hexdigest()
    return Attestation(passport='backend/tests/fixtures/synthetic-passport.md', fixture='backend/tests/fixtures/synthetic-source.txt',
                       fixture_sha256=digest, original_sha256=digest, source_url=url, year=2026, kind='archive', sample_rows=4,
                       checked_rows=4, verified_at=NOW, adapter_version=version)


@pytest.mark.parametrize(('version', 'url', 'body', 'charset'), [(JSON_VERSION, JSON_URL, json_body(), 'utf-8'), (CSV_VERSION, CSV_URL, csv_body(), 'cp1251')])
def test_json_and_csv_decode_to_the_same_rows(version, url, body, charset):
    parsed = parse_structured(response(url, body, charset), binding(url, version), SECRET, profile(version, url))
    rows = parsed.entries
    assert [r.official_rank for r in rows] == [1, 2, 3, 4] and parsed.expected_rows == 4 and parsed.seats == 10
    assert [str(r.score) for r in rows] == ['299', '298', '297', '296']
    assert [r.consent for r in rows] == [True, False, True, False]
    assert [r.priority for r in rows] == [1, 1, None, None] and rows[3].participation == 'enrolled'
    assert 'A-001' not in parsed.model_dump_json() and 'unknown_priority' in parsed.warnings


def broken_json():
    items = records()
    return [json.dumps({'data': {'items': records(3)}}).encode(),                      # declared count differs
            json.dumps({'data': {'items': items[1:] + items[:1]}}).encode(),           # official order broken
            json.dumps({'data': {'items': [dict(items[0], id='A-001')] * 4}}).encode(),  # duplicate code
            json.dumps({'data': {'items': [dict(r, agree='возможно') for r in items]}}).encode(),
            json.dumps({'data': {'items': [dict(r, ball={'x': 1}) for r in items]}}).encode(),
            json.dumps({'data': {'rows': items}}).encode(),
            b'{"data": {"items": [NaN]}}', b'<html>captcha</html>']


@pytest.mark.parametrize('body', broken_json())
def test_unexpected_json_fails_the_whole_list(body):
    with pytest.raises(AdapterError, match='invalid_format'):
        parse_structured(response(JSON_URL, body), binding(JSON_URL, JSON_VERSION), SECRET, profile(JSON_VERSION, JSON_URL))


@pytest.mark.parametrize('body', [csv_body(delimiter=','), csv_body()[:-30], ('№;Код\n1;A-1\n').encode('cp1251'), csv_body(records()[:3])])
def test_unexpected_csv_fails_the_whole_list(body):
    with pytest.raises(AdapterError, match='invalid_format'):
        parse_structured(response(CSV_URL, body, 'cp1251'), binding(CSV_URL, CSV_VERSION), SECRET, profile(CSV_VERSION, CSV_URL))


def test_profile_and_adapter_declarations_are_strict():
    with pytest.raises(ValueError):
        profile(JSON_VERSION, JSON_URL, fields=(('rank', 'n'),))
    with pytest.raises(ValueError):
        make_structured_adapter(SECRET, [profile(JSON_VERSION, JSON_URL)], version=JSON_VERSION)  # attested needs a proof
    with pytest.raises(AdapterError, match='invalid_binding'):
        parse_structured(response(JSON_URL, json_body()), replace(binding(JSON_URL, JSON_VERSION), year=2025), SECRET, profile(JSON_VERSION, JSON_URL))
    adapter = make_structured_adapter(SECRET, [profile(JSON_VERSION, JSON_URL, proof=proof(JSON_VERSION, JSON_URL, json_body()))], version=JSON_VERSION)
    assert adapter.attested and adapter.version == JSON_VERSION
    assert Registry((adapter,)).resolve(binding(JSON_URL, JSON_VERSION)) is adapter


@pytest.mark.parametrize(('version', 'url', 'good', 'bad', 'charset'), [
    (JSON_VERSION, JSON_URL, json_body(), json_body(records(3)), 'utf-8'),
    (CSV_VERSION, CSV_URL, csv_body(), csv_body(records(3)), 'cp1251')])
def test_worker_imports_once_and_a_bad_list_keeps_the_last_valid_snapshot(postgres_engine, tmp_path, version, url, good, bad, charset):  # noqa: F811
    adapter = make_structured_adapter(SECRET, [profile(version, url, proof=proof(version, url, good))], version=version)
    registry = Registry((adapter,))
    seed_source(postgres_engine, url=url, adapter_version=version)
    store = RawStore(tmp_path/'raw')
    at = clock()
    def fetch_with(body):
        return lambda *_, **__: FetchResult(url, body, 'text/plain', hashlib.sha256(body).hexdigest(), at, charset)
    enqueue(postgres_engine, 'source-1', now=at)
    assert run_once(postgres_engine, store, registry=registry, now=lambda: at, fetch=fetch_with(good))['state'] == 'success'
    with Session(postgres_engine) as db:
        first = db.get(PublishedSnapshot, 'source-1').snapshot_id
        db.get(SourceJob, 'source-1').next_run_at = at
        db.commit()
    # The same payload again is the same snapshot, not a second copy.
    assert run_once(postgres_engine, store, registry=registry, now=lambda: at, fetch=fetch_with(good))['state'] == 'success'
    with Session(postgres_engine) as db:
        assert db.scalar(select(func.count()).select_from(SourceSnapshot)) == 1
        assert db.scalar(select(func.count()).select_from(CandidateEntry)) == 4
        db.get(SourceJob, 'source-1').next_run_at = at
        db.commit()
    result = run_once(postgres_engine, store, registry=registry, now=lambda: at, fetch=fetch_with(bad))
    assert result['state'] == 'failed'
    with Session(postgres_engine) as db:
        assert db.get(PublishedSnapshot, 'source-1').snapshot_id == first
        assert db.scalar(select(func.count()).select_from(CandidateEntry)) == 4


def test_mass_enqueue_spreads_domains_and_never_duplicates(postgres_engine):  # noqa: F811
    from app.admissions import Source
    from app.sources.registry import Adapter
    from source_helpers import parsed
    seed_source(postgres_engine)
    with Session(postgres_engine) as db:
        for index, domain in enumerate(['example.org', 'example.org', 'example.com', 'example.org']):
            db.add(Source(id=f'mass-{index}', group_id='group-1', url=f'https://{domain}/list-{index}', domain=domain,
                          adapter_version='synthetic-v1' if index < 3 else 'unknown-v1', snapshot_kind='archive', enabled=True))
        db.add(Source(id='off', group_id='group-1', url='https://example.org/off', domain='example.org', adapter_version='synthetic-v1',
                      snapshot_kind='archive', enabled=False))
        db.commit()
    registry = Registry((Adapter('synthetic-v1', frozenset({'example.org', 'example.com'}), lambda response, binding: parsed()),))
    now = clock()
    # Production rules: nothing unattested is ever queued.
    assert enqueue_all(postgres_engine, registry=registry, now=now) == dict(
        sources=5, queued=0, deferred=0, skipped={'adapter_unavailable': 1, 'unattested_adapter': 4}, domains=0)
    first = enqueue_all(postgres_engine, registry=registry, now=now, spread_seconds=60, allow_unattested=True)
    assert first == dict(sources=5, queued=4, deferred=0, skipped={'adapter_unavailable': 1}, domains=2)
    with Session(postgres_engine) as db:
        starts = {job.source_id: (job.next_run_at - now).total_seconds() for job in db.scalars(select(SourceJob)).all()}
    assert sorted(v for k, v in starts.items() if k != 'mass-2') == [0, 60, 120] and starts['mass-2'] == 0
    assert 'off' not in starts and 'mass-3' not in starts
    again = enqueue_all(postgres_engine, registry=registry, now=now, allow_unattested=True)
    assert again['queued'] == 0 and again['deferred'] == 4
    with Session(postgres_engine) as db:
        assert db.scalar(select(func.count()).select_from(SourceJob)) == 4
    with pytest.raises(ValueError):
        enqueue_all(postgres_engine, registry=registry, now=now, spread_seconds=-1)
