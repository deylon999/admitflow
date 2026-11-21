"""Resume bounded programme acquisition or explicitly publish reviewed originals."""
import argparse
from contextlib import nullcontext
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import tempfile
import time
from urllib.parse import unquote, urlsplit

from sqlalchemy.exc import SQLAlchemyError

from app.catalog.program_catalog_batch_fetch import bounded_fetch
from app.catalog.program_catalog_import import import_document, read_original, require_import_schema
from app.catalog.program_catalog_sources import select_sources
from app.sources.fetcher import DEFAULT_SOURCE_BYTES, FetchError, FetchPolicy
from app.sources.storage import RawStore, StorageError


MAX_ATTEMPTS = 3
MAX_PER_RUN = 10
MIN_DELAY = 2
IN_PROGRESS_COOLDOWN = 90
MAX_ROBOTS_BYTES = 256 * 1024
TRANSIENT = {'timeout', 'network_error', 'dns_unavailable', 'rate_limited', 'http_error', 'incomplete_response'}


def robots_delay(body, charset, url):
    """Honor applicable deny rules conservatively, including wildcards and query paths."""
    if body.lstrip().startswith(b'<'):
        raise ValueError('invalid_robots_document')
    try:
        lines = body.decode(charset or 'utf-8-sig', errors='strict').splitlines()
    except (UnicodeError, LookupError):
        raise ValueError('invalid_robots_document') from None
    groups = []
    agents, rules = [], []
    for line in lines:
        field, separator, value = line.split('#', 1)[0].partition(':')
        if not separator:
            continue
        field, value = field.strip().lower(), value.strip()
        if field == 'user-agent':
            if rules:
                groups.append((agents, rules))
                agents, rules = [], []
            if value:
                agents.append(value.lower())
        elif agents and field in ('allow', 'disallow', 'crawl-delay', 'request-rate'):
            rules.append((field, value))
    if agents:
        groups.append((agents, rules))
    if not groups:
        raise ValueError('invalid_robots_document')
    parsed = urlsplit(url)
    target = unquote(parsed.path + ('?' + parsed.query if parsed.query else ''))
    delay = MIN_DELAY
    for agents, rules in groups:
        if not any(a == '*' or 'admitflow/0.2'.startswith(a) for a in agents):
            continue
        for field, value in rules:
            if field == 'disallow' and value:
                anchored = value.endswith('$')
                parts = (value[:-1] if anchored else value).split('*')
                # Match the literals consecutively without regex backtracking.
                pattern = [unquote(part) for part in parts]
                remainder = target[len(pattern[0]):] if target.startswith(pattern[0]) else None
                for part in pattern[1:-1]:
                    if remainder is None or (index := remainder.find(part)) < 0:
                        remainder = None
                        break
                    remainder = remainder[index + len(part):]
                tail = pattern[-1] if len(pattern) > 1 else ''
                if remainder is None:
                    continue
                if anchored and (remainder == '' if len(pattern) == 1 else remainder.endswith(tail)):
                    raise ValueError('robots_disallowed')
                if not anchored and tail in remainder:
                    raise ValueError('robots_disallowed')
            if field == 'crawl-delay':
                if not re.fullmatch(r'[0-9]{1,6}(\.[0-9]{1,6})?', value):
                    raise ValueError('invalid_robots_document')
                delay = max(delay, math.ceil(float(value)))
            if field == 'request-rate':
                rate = re.fullmatch(r'([1-9][0-9]{0,5})/([1-9][0-9]{0,5})', value)
                if not rate:
                    raise ValueError('invalid_robots_document')
                delay = max(delay, math.ceil(int(rate[2])/int(rate[1])))
    if delay > 60:
        raise ValueError('source_requires_longer_delay')
    return delay


def _state_path(store):
    path = store.root / 'batch-state.json'
    if path.is_symlink():
        raise StorageError('unsafe_storage_path')
    return path


def _load_state(store):
    path = _state_path(store)
    if not path.exists():
        return {'format': 1, 'sources': {}, 'hosts': {}}
    with path.open('rb') as file:
        raw = file.read(16*1024*1024 + 1)
    try:
        if len(raw) > 16*1024*1024:
            raise ValueError()
        state = json.loads(raw)
        if state['format'] != 1 or not all(isinstance(state[k], dict) for k in ('sources', 'hosts')):
            raise ValueError()
        return state
    except (ValueError, TypeError, KeyError) as error:
        raise StorageError('catalog_invalid_batch_checkpoint') from error


def _save_state(store, state):
    path = _state_path(store)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=store.root, prefix='.batch-', delete=False) as file:
            temporary = Path(file.name)
            file.write(json.dumps(state, sort_keys=True, allow_nan=False).encode() + b'\n')
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _scope(source):
    return {'key': source.key, 'year': source.year, 'universityId': source.university_id, 'url': source.url}


def _matches(source, entry):
    return all(entry.get(key) == value for key, value in _scope(source).items())


def _fetch(url, *, maximum, content_types):
    host = urlsplit(url).hostname
    policy = FetchPolicy(frozenset({host}), max_bytes=maximum, timeout=15,
                         max_redirects=0, content_types=frozenset(content_types))
    return bounded_fetch(url, policy)


def _capture(source, store, fetch, pause):
    robots_url = f'https://{source.host}/robots.txt'
    robots = fetch(robots_url, maximum=MAX_ROBOTS_BYTES, content_types={'text/plain'})
    if robots.url != robots_url:
        raise ValueError('unexpected_source_redirect')
    delay = robots_delay(robots.body, robots.charset, source.url)
    store.put(robots.body, robots.payload_hash)
    pause(delay)
    result = fetch(source.url, maximum=DEFAULT_SOURCE_BYTES, content_types={'text/html'})
    if result.url != source.url or result.content_type != 'text/html':
        raise ValueError('unexpected_source_response')
    store.put(result.body, result.payload_hash)
    return dict(sha256=result.payload_hash, bytes=len(result.body), contentType=result.content_type,
                fetchedAt=result.fetched_at.isoformat(), finalUrl=result.url,
                robotsUrl=robots_url, robotsSha256=robots.payload_hash,
                robotsFetchedAt=robots.fetched_at.isoformat(), crawlDelay=delay)


def _capture_status(source, entry):
    if entry['status'] != 'captured':
        return entry
    review = source.review
    eligible = review is not None and review['verification_status'] == 'verified' and review['original_sha256'] == entry['sha256']
    return entry | {'publication': 'eligible' if eligible else 'review_required'}


def capture_batch(sources, store, *, limit=MAX_PER_RUN, fetch=_fetch, pause=time.sleep, clock=time.time):
    if type(limit) is not int or not 1 <= limit <= MAX_PER_RUN:
        raise ValueError('catalog_invalid_batch_limit')
    if not sources:
        raise ValueError('catalog_empty_source_batch')
    items, started = [], 0
    with store.locked(timeout=0):
        state = _load_state(store)
        for source in sources:
            scope = _scope(source)
            previous = state['sources'].get(source.key)
            if previous is not None and not _matches(source, previous):
                items.append(scope | {'status': 'blocked', 'error': 'catalog_batch_scope_conflict'})
                continue
            if previous and previous['status'] == 'captured':
                try:
                    store.read(previous['sha256'])
                    store.read(previous['robotsSha256'])
                except StorageError as error:
                    items.append(scope | {'status': 'blocked', 'error': error.code})
                else:
                    items.append(_capture_status(source, previous) | {'reused': True})
                continue
            if previous and previous['status'] == 'blocked':
                items.append(previous)
                continue
            attempts = previous['attempts'] if previous else 0
            if attempts >= MAX_ATTEMPTS:
                items.append(scope | {'status': 'blocked', 'attempts': attempts, 'error': 'retry_limit_reached'})
                continue
            eligible_at = state['hosts'].get(source.host, 0)
            if eligible_at > clock():
                items.append(scope | {'status': 'deferred', 'notBefore': eligible_at, 'attempts': attempts,
                                     'error': previous.get('error') if previous else None})
                continue
            if started >= limit:
                items.append(scope | {'status': 'pending', 'attempts': attempts})
                continue
            started += 1
            entry = scope | {'attempts': attempts + 1, 'status': 'running'}
            state['sources'][source.key] = entry
            state['hosts'][source.host] = clock() + IN_PROGRESS_COOLDOWN
            _save_state(store, state)
            def paced_pause(delay):
                # A crash while waiting or during the document request leaves a
                # durable host reservation extending beyond the required delay.
                state['hosts'][source.host] = clock() + delay + IN_PROGRESS_COOLDOWN
                _save_state(store, state)
                pause(delay)
            try:
                data = _capture(source, store, fetch, paced_pause)
            except FetchError as error:
                retry = error.code in TRANSIENT and error.retry_after is not None
                wait = max(15 * 2**attempts, error.retry_after or 0) if retry else MIN_DELAY
                entry.update(status='deferred' if retry and entry['attempts'] < MAX_ATTEMPTS else 'blocked', error=error.code)
                # Keep an interrupted robots/document reservation when larger
                # than the suggested retry time, so bursts cannot bypass pacing.
                state['hosts'][source.host] = max(state['hosts'][source.host], clock() + wait)
                if entry['status'] == 'deferred':
                    entry['notBefore'] = state['hosts'][source.host]
            except (ValueError, StorageError) as error:
                entry.update(status='blocked', error=str(error))
            else:
                entry.update(status='captured', **data)
                state['hosts'][source.host] = clock() + data['crawlDelay']
            _save_state(store, state)
            items.append(_capture_status(source, entry))
    return {'phase': 'capture', 'attemptedSources': started, 'selectedSources': len(sources),
            'allSourcesSucceeded': all(x['status'] == 'captured' for x in items),
            'completeUniversityCatalog': False, 'items': items}


def publish_batch(engine, sources, raw_store, *, captured=None, originals=None):
    """Use DB pointers as publication checkpoints and recheck reviewed bytes on every replay."""
    if (captured is None) == (originals is None) or (captured and captured.root == raw_store.root):
        raise ValueError('catalog_select_one_originals_store')
    if not sources:
        raise ValueError('catalog_empty_source_batch')
    items = []
    with captured.locked(timeout=0) if captured else nullcontext():
        entries = _load_state(captured)['sources'] if captured else None
        for source in sources:
            result = _scope(source)
            review = source.review
            if review is None or review['verification_status'] != 'verified':
                items.append(result | {'outcome': 'review_required', 'error': 'catalog_unreviewed_document'})
                continue
            body = None
            if entries is not None:
                entry = entries.get(source.key, {})
                if not _matches(source, entry) or entry.get('status') != 'captured':
                    items.append(result | {'outcome': 'unavailable', 'error': 'catalog_capture_unavailable'})
                    continue
                if entry['sha256'] != review['original_sha256']:
                    items.append(result | {'outcome': 'review_required', 'error': 'catalog_original_hash_mismatch',
                                           'capturedSha256': entry['sha256']})
                    continue
                try:
                    body = captured.read(entry['sha256'])
                    captured.read(entry['robotsSha256'])
                except StorageError as error:
                    items.append(result | {'outcome': 'unavailable', 'error': error.code})
                    continue
            else:
                body = read_original(originals, review)
            items.append(result | import_document(engine, review, body, raw_store))
    return {'phase': 'publish', 'atomicPerDocument': True, 'selectedSources': len(sources),
            'allSourcesSucceeded': all(item['outcome'] in ('published', 'unchanged') for item in items),
            'completeUniversityCatalog': False, 'items': items}


def main(argv=None):
    from app.core.config import Settings
    from app.database import make_engine
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='phase', required=True)
    capture = commands.add_parser('capture')
    capture.add_argument('--work-dir', type=Path, required=True)
    capture.add_argument('--limit', type=int, default=3)
    publish = commands.add_parser('publish')
    source = publish.add_mutually_exclusive_group(required=True)
    source.add_argument('--captured', type=Path)
    source.add_argument('--reviewed-originals', type=Path)
    publish.add_argument('--raw-store', type=Path, required=True)
    for command in (capture, publish):
        command.add_argument('--year', type=int, required=True)
        command.add_argument('--source', action='append', dest='keys')
    args = parser.parse_args(argv)
    try:
        sources = select_sources(args.year, args.keys)
        if args.phase == 'capture':
            result = capture_batch(sources, RawStore(args.work_dir, max_bytes=DEFAULT_SOURCE_BYTES), limit=args.limit)
        else:
            engine = make_engine(Settings.from_env().database_url)
            try:
                require_import_schema(engine)
                captured = RawStore(args.captured) if args.captured else None
                result = publish_batch(engine, sources, RawStore(args.raw_store),
                                       captured=captured, originals=args.reviewed_originals)
            finally:
                engine.dispose()
    except (ValueError, StorageError) as error:
        code = str(error)
        print(json.dumps({'phase': args.phase, 'error': code if re.fullmatch(r'[a-z0-9_]+', code) else 'catalog_batch_failed'}))
        return 1
    except (OSError, SQLAlchemyError):
        print(json.dumps({'phase': args.phase, 'error': 'catalog_batch_interrupted', 'resumeSafe': True}))
        return 1
    print(json.dumps(result | {'year': args.year}, ensure_ascii=True))
    return 0 if result['allSourcesSucceeded'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
