"""Research capture must respect robots and preserve prior originals on errors."""
from datetime import datetime, timezone
import hashlib
import importlib.util
from pathlib import Path

import pytest

from app.sources.fetcher import FetchError, FetchResult

spec = importlib.util.spec_from_file_location('capture_program_catalog', Path(__file__).resolve().parents[2] / 'scripts/data/capture_program_catalog.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def response(url, body):
    return FetchResult(url, body, 'text/plain' if url.endswith('robots.txt') else 'text/html',
                       hashlib.sha256(body).hexdigest(), datetime(2026, 11, 21, tzinfo=timezone.utc), 'utf-8')


def test_serial_bounded_capture_preserves_content_addressed_documents(tmp_path):
    requests, waits = [], []
    def fetch(url):
        requests.append(url)
        return response(url, b'User-agent: *\nAllow: /\nCrawl-delay: 3' if url.endswith('robots.txt') else b'<p>Synthetic programme</p>')
    first = module.capture('hse-design-2027', tmp_path, fetch=fetch, pause=waits.append)
    second = module.capture('hse-design-2027', tmp_path, fetch=fetch, pause=waits.append)
    assert first == second and waits == [3, 3]
    assert len(requests) == 4 and requests[0].endswith('robots.txt')
    assert len(list(tmp_path.glob('*.html'))) == 1
    assert hashlib.sha256(next(tmp_path.glob('*.html')).read_bytes()).hexdigest() == first['sha256']


@pytest.mark.parametrize('robots,error', [
    (b'User-agent: *\nDisallow: /', 'robots_disallowed'),
    (b'<html>Authentication required</html>', 'invalid_robots_document'),
    (b'User-agent: *\nCrawl-delay: 90', 'source_requires_longer_delay'),
])
def test_disallow_or_invalid_robots_never_fetches_document(tmp_path, robots, error):
    requests = []
    def fetch(url):
        requests.append(url)
        return response(url, robots)
    with pytest.raises(ValueError, match=error):
        module.capture('sgu-seats-2026', tmp_path, fetch=fetch, pause=lambda _: None)
    assert len(requests) == 1 and list(tmp_path.iterdir()) == []


def test_source_error_keeps_previous_capture_without_retry(tmp_path):
    old = tmp_path / 'previous.html'
    old.write_bytes(b'old')
    requests = []
    def fetch(url):
        requests.append(url)
        if not url.endswith('robots.txt'):
            raise FetchError('access_denied')
        return response(url, b'User-agent: *\nAllow: /')
    with pytest.raises(FetchError):
        module.capture('sgu-seats-2026', tmp_path, fetch=fetch, pause=lambda _: None)
    assert len(requests) == 2 and old.read_bytes() == b'old'
    assert list(tmp_path.iterdir()) == [old]
