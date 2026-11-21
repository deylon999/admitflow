"""Bounded programme batch tests with fake transport and native publication."""
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import time

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.program_catalog_batch import capture_batch, publish_batch, robots_delay
from app.program_catalog_batch_fetch import bounded_fetch
from app.program_catalog_models import ProgramCatalogPublication, ProgramCatalogRevision
from app.program_catalog_sources import ProgrammeSource, select_sources
from app.sources.fetcher import FetchError, FetchPolicy, FetchResult
from app.sources.storage import RawStore
from native_support import postgres_engine  # noqa: F401
from test_program_catalog_import import source


ROBOTS = b'User-agent: *\nDisallow:\nCrawl-delay: 2\n'
FIRST = ProgrammeSource('first', 'miccedu-1766', 2027, 'https://example.org/first')
SECOND = ProgrammeSource('second', 'miccedu-1507', 2027, 'https://other.example.org/second')


class Clock:
    now = 1_800_000_000

    def time(self):
        return self.now

    def pause(self, delay):
        self.now += delay


def response(url, body):
    mime = 'text/plain' if url.endswith('/robots.txt') else 'text/html'
    return FetchResult(url, body, mime, hashlib.sha256(body).hexdigest(), datetime.now(timezone.utc), 'utf-8')


def test_registry_separates_campaigns_and_rejects_unknown_keys():
    assert {s.key for s in select_sources(2027)} == {
        'hse-design-2027', 'itmo-announcements-2027', 'rudn-admission-2027', 'sfu-admission-2027'}
    assert [s.key for s in select_sources(2026)] == ['sgu-seats-2026']
    for keys in (['sgu-seats-2026'], ['hse-design-2027']*2, []):
        with pytest.raises(ValueError):
            select_sources(2027, keys)


@pytest.mark.parametrize('robots,error', [
    (b'User-agent: *\nAllow: /\nDisallow: /*?restricted=*', 'robots_disallowed'),
    (b'User-agent: AdmitFlow\nDisallow: /f%69rst$', 'robots_disallowed'),
    (b'User-agent: *\nCrawl-delay: 60.1', 'source_requires_longer_delay'),
    (b'User-agent: *\nRequest-rate: 1/120', 'source_requires_longer_delay'),
    (b'<html>\nUser-agent: *\n</html>', 'invalid_robots_document'),
])
def test_robots_blocks_unsafe_paths_or_unsupported_waits(robots, error):
    url = FIRST.url + '?restricted=true' if b'?' in robots else FIRST.url
    with pytest.raises(ValueError, match=error):
        robots_delay(robots, 'utf-8', url)


def test_robots_matches_anchored_paths_and_rounds_up_delay():
    robots = b'User-agent: *\nDisallow: /first$\nRequest-rate: 2/7\nCrawl-delay: 3.1'
    assert robots_delay(robots, 'utf-8', FIRST.url + '?visible=1') == 4


def test_batch_limit_resume_and_hash_revalidation(tmp_path):
    store = RawStore(tmp_path/'capture')
    clock = Clock()
    requests = []
    def fetch(url, **kw):
        requests.append((url, kw, clock.now))
        return response(url, ROBOTS if url.endswith('/robots.txt') else b'<p>candidate</p>')
    kwargs = dict(limit=1, fetch=fetch, pause=clock.pause, clock=clock.time)
    first = capture_batch([FIRST,SECOND], store, **kwargs)
    assert [r['status'] for r in first['items']] == ['captured','pending']
    assert first['items'][0]['publication'] == 'review_required'
    assert not first['allSourcesSucceeded']
    assert [(u, t) for u, _, t in requests] == [('https://example.org/robots.txt', clock.now-2), (FIRST.url, clock.now)]
    assert requests[0][1]['maximum'] == 256*1024 and requests[1][1]['maximum'] == 5*1024*1024
    last = capture_batch([FIRST,SECOND], store, **kwargs)
    assert last['allSourcesSucceeded'] and not last['completeUniversityCatalog']
    assert last['items'][0]['reused'] and last['attemptedSources'] == 1 and len(requests) == 4
    third = capture_batch([FIRST,SECOND], store, **kwargs)
    assert third['attemptedSources'] == 0 and len(requests) == 4
    (store.root/third['items'][0]['sha256']).write_bytes(b'corrupt')
    broken = capture_batch([FIRST,SECOND], store, **kwargs)
    assert broken['items'][0]['error'] == 'raw_hash_mismatch'
    assert not broken['allSourcesSucceeded'] and len(requests) == 4


def test_batch_limit_does_not_cap_total_registry_size(tmp_path):
    sources = [replace(FIRST, key=f'source-{i}', url=f'https://source-{i}.example.org/admission') for i in range(13)]
    store = RawStore(tmp_path/'capture')
    requests = []
    def fetch(url, **_):
        requests.append(url)
        return response(url, ROBOTS)
    first = capture_batch(sources, store, limit=10, pause=lambda _: None, fetch=fetch)
    assert first['attemptedSources'] == 10 and not first['allSourcesSucceeded']
    second = capture_batch(sources, store, limit=10, pause=lambda _: None, fetch=fetch)
    assert second['attemptedSources'] == 3 and second['allSourcesSucceeded']
    assert sum(item.get('reused', False) for item in second['items']) == 10
    assert len(requests) == len(set(requests)) == 26


def test_transient_failure_backs_off_by_host_and_keeps_other_sources_running(tmp_path):
    clock, store = Clock(), RawStore(tmp_path/'capture')
    same = replace(FIRST, key='same-host', url='https://example.org/other')
    requests = []
    def fetch(url, **_):
        requests.append(url)
        if url == FIRST.url:
            raise FetchError('rate_limited', retry_after=120)
        return response(url, ROBOTS if url.endswith('/robots.txt') else b'<p>other</p>')
    kwargs = dict(fetch=fetch, pause=clock.pause, clock=clock.time)
    first = capture_batch([FIRST,same,SECOND], store, **kwargs)
    assert [r['status'] for r in first['items']] == ['deferred','deferred','captured']
    assert first['items'][0]['notBefore'] == first['items'][1]['notBefore'] >= clock.now+118
    assert same.url not in requests
    assert capture_batch([FIRST], store, **kwargs)['attemptedSources'] == 0
    for _ in range(2):
        clock.pause(130)
        last = capture_batch([FIRST], store, **kwargs)
    assert last['items'][0]['status'] == 'blocked' and last['items'][0]['attempts'] == 3
    clock.pause(500)
    assert capture_batch([FIRST], store, **kwargs)['attemptedSources'] == 0
    assert requests.count(FIRST.url) == 3


def test_interruption_is_resumed_after_durable_host_cooldown(tmp_path):
    clock, store = Clock(), RawStore(tmp_path/'capture')
    def interrupted(url, **_):
        if url == SECOND.url:
            raise KeyboardInterrupt
        return response(url, ROBOTS if url.endswith('/robots.txt') else b'<p>first</p>')
    kwargs = dict(pause=clock.pause, clock=clock.time)
    with pytest.raises(KeyboardInterrupt):
        capture_batch([FIRST,SECOND], store, fetch=interrupted, **kwargs)
    cooldown = capture_batch([FIRST,SECOND], store, fetch=interrupted, **kwargs)
    assert cooldown['items'][0]['reused'] and cooldown['items'][1]['status'] == 'deferred'
    clock.pause(100)
    result = capture_batch([FIRST,SECOND], store, fetch=lambda u, **kw: response(u, ROBOTS), **kwargs)
    assert result['allSourcesSucceeded'] and result['attemptedSources'] == 1
    assert result['items'][1]['attempts'] == 2


def test_denials_and_unreviewed_redirects_never_retry(tmp_path):
    clock, store = Clock(), RawStore(tmp_path/'capture')
    calls = []
    def fetch(url, **_):
        calls.append(url)
        if url == FIRST.url:
            raise FetchError('access_denied')
        return response(SECOND.url if url.startswith('https://other.') else url, ROBOTS)
    kwargs = dict(fetch=fetch, pause=clock.pause, clock=clock.time)
    result = capture_batch([FIRST,SECOND], store, **kwargs)
    assert [r['error'] for r in result['items']] == ['access_denied','unexpected_source_redirect']
    clock.pause(500)
    assert capture_batch([FIRST,SECOND], store, **kwargs)['attemptedSources'] == 0
    assert len(calls) == 3


def stalled_download(url, policy, folder):
    (folder/'body').write_bytes(b'incomplete staged response')
    time.sleep(20)


def test_fetch_deadline_covers_stalled_child_even_with_partial_bytes(monkeypatch):
    monkeypatch.setattr('app.program_catalog_batch_fetch._download', stalled_download)
    started = time.monotonic()
    with pytest.raises(FetchError, match='timeout'):
        bounded_fetch(FIRST.url, FetchPolicy(frozenset({FIRST.host})), timeout=0.25)
    assert time.monotonic() - started < 5


def reviewed(kind):
    body, review = source(kind)
    return body, ProgrammeSource(review['key'], review['university_id'], review['year'], review['url'], review)


@pytest.mark.postgres
def test_publication_uses_exact_reviewed_capture_and_quarantines_new_bytes(postgres_engine, tmp_path):
    body, hse = reviewed('hse')
    pending = select_sources(2027, ['itmo-announcements-2027'])[0]
    staged, published = RawStore(tmp_path/'capture'), RawStore(tmp_path/'raw')
    def capture_at(store, payload):
        return capture_batch([hse,pending], store, pause=lambda _: None, fetch=lambda url, **kw:
                             response(url, ROBOTS if url.endswith('/robots.txt') else payload))
    capture_at(staged, body)
    first = publish_batch(postgres_engine,[hse,pending],published,captured=staged)
    assert [r['outcome'] for r in first['items']] == ['published','review_required']
    assert not first['allSourcesSucceeded'] and not first['completeUniversityCatalog']
    repeat = publish_batch(postgres_engine,[hse],published,captured=staged)
    assert repeat['items'][0]['outcome'] == 'unchanged'
    assert repeat['items'][0]['revisionId'] == first['items'][0]['revisionId']
    changed = RawStore(tmp_path/'changed')
    capture_at(changed, body + b' ')
    result = publish_batch(postgres_engine,[hse],published,captured=changed)
    assert result['items'][0]['error'] == 'catalog_original_hash_mismatch'
    with Session(postgres_engine) as db:
        assert db.scalar(select(ProgramCatalogPublication.revision_id)) == first['items'][0]['revisionId']
        assert db.scalar(select(func.count()).select_from(ProgramCatalogRevision)) == 1


@pytest.mark.postgres
def test_original_batch_isolates_missing_sources_and_replays_in_database(postgres_engine, tmp_path):
    hse_body, hse = reviewed('hse')
    sgu_body, sgu = reviewed('sgu')
    other = replace(hse, key='synthetic-unavailable', review=hse.review | {'original_sha256': 'a'*64})
    originals, raw_store = tmp_path/'originals', RawStore(tmp_path/'raw')
    originals.mkdir()
    for entry, data in ((hse,hse_body),(sgu,sgu_body)):
        (originals/(entry.review['original_sha256']+'.html')).write_bytes(data)
    first = publish_batch(postgres_engine,[other,hse],raw_store,originals=originals)
    assert [r['outcome'] for r in first['items']] == ['rejected','published']
    assert not first['allSourcesSucceeded']
    archive = publish_batch(postgres_engine,[sgu],raw_store,originals=originals)
    assert archive['items'][0]['outcome'] == 'published'
    repeat = publish_batch(postgres_engine,[hse],raw_store,originals=originals)
    assert repeat['items'][0]['outcome'] == 'unchanged'
    assert repeat['items'][0]['revisionId'] == first['items'][1]['revisionId']
    with Session(postgres_engine) as db:
        assert db.scalar(select(func.count()).select_from(ProgramCatalogRevision)) == 2
        assert db.scalar(select(func.count()).select_from(ProgramCatalogPublication)) == 2


def test_batch_cli_rejects_sqlite_before_creating_storage(tmp_path, monkeypatch, capsys):
    from app.program_catalog_batch import main
    database, raw = tmp_path/'should-not-exist.db', tmp_path/'raw'
    monkeypatch.setenv('DATABASE_URL', f'sqlite:///{database}')
    assert main(['publish','--year','2027','--reviewed-originals',str(tmp_path),'--raw-store',str(raw)]) == 1
    assert 'catalog_import_requires_postgresql' in capsys.readouterr().out
    assert not database.exists() and not raw.exists()
