"""Bounded, explicit capture of approved public programme documents only.

Run with backend/.venv/Scripts/python.exe. Never downloads applicant pages.
Original bytes are private research artifacts, not Git fixtures or verification.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
from app.catalog.program_catalog_sources import load_sources
from app.sources.fetcher import Fetcher, FetchPolicy

SOURCES = {source.key:source for source in load_sources() if source.review}


def capture(key, output, *, fetch=None, pause=time.sleep):
    source = SOURCES[key]
    url = source.url
    domain = urlsplit(url).hostname
    fetch = fetch or Fetcher(FetchPolicy(frozenset({domain}), timeout=15, max_redirects=0,
        content_types=frozenset({'text/plain', source.content_type}))).fetch
    output = Path(output)
    # All failures leave any previous successful capture intact.
    robots_url = f'https://{domain}/robots.txt'
    robots = fetch(robots_url)
    if robots.url != robots_url or robots.content_type != 'text/plain':
        raise ValueError('unexpected_robots_response')
    parser = RobotFileParser(robots_url)
    lines = robots.body.decode(robots.charset or 'utf-8', errors='strict').splitlines()
    if not any(line.strip().lower().startswith('user-agent:') for line in lines):
        raise ValueError('invalid_robots_document')
    parser.parse(lines)
    if not parser.can_fetch('AdmitFlow/0.2', url):
        raise ValueError('robots_disallowed')
    delay = max(2, parser.crawl_delay('AdmitFlow/0.2') or parser.crawl_delay('*') or 0)
    # Research is deliberately serial with a finite wait, no automatic retries.
    if delay > 60:
        raise ValueError('source_requires_longer_delay')
    pause(delay)
    result = fetch(url)
    if result.url != url or result.content_type != source.content_type:
        raise ValueError('unexpected_source_response')
    output.mkdir(parents=True, exist_ok=True)
    # Content addressing preserves old documents when a source changes.
    suffix = '.pdf' if source.content_type == 'application/pdf' else '.html'
    for response, suffix in [(robots, '.robots'), (result, suffix)]:
        if hashlib.sha256(response.body).hexdigest() != response.payload_hash:
            raise ValueError('capture_hash_mismatch')
        path = output / (response.payload_hash + suffix)
        if path.exists():
            if hashlib.sha256(path.read_bytes()).hexdigest() != response.payload_hash:
                raise ValueError('capture_cache_corrupt')
        else:
            path.write_bytes(response.body)
    manifest = dict(key=key, url=url, finalUrl=result.url, contentType=result.content_type,
        sha256=result.payload_hash, fetchedAt=result.fetched_at.isoformat(), bytes=len(result.body),
        charset=result.charset, robotsUrl=robots_url, robotsSha256=robots.payload_hash,
        robotsFetchedAt=robots.fetched_at.isoformat(), robotsAllowed=True, crawlDelay=delay,
        status='captured', policy='one document request after robots; no retries or access bypass')
    path = output / (key + '-' + result.payload_hash + '.json')
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', choices=sorted(SOURCES))
    parser.add_argument('--output', type=Path, default=ROOT / 'backend/var/research/program-catalog')
    args = parser.parse_args(argv)
    print(json.dumps(capture(args.source, args.output), ensure_ascii=True))


if __name__ == '__main__':
    main()
