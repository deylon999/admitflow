"""Capture MICCEDU institution pages of past monitoring editions for KAN-232.

Fetches /iam/<edition>/_vpo/inst.php?id=<id> for every head organisation of the
2025 catalog and editions 2016-2025, keeps the page hash and only the tables
the dataset needs (institution info, education indicators, result series),
and writes JSON lines (gzip) for scripts/build_admission_history.py.

The site is reachable from Russian networks only. Two workers with a pause
after every request, as in scripts/capture_catalog.py. Already captured pages
are skipped, so an interrupted run can continue.

Usage:
    python scripts/capture_admission_history.py --output capture.jsonl.gz [--editions 2016-2025]
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import threading
import time
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

from build_admission_history import CATALOG, EDITIONS

PAGE = 'https://monitoring.miccedu.ru/iam/{edition}/_vpo/inst.php?id={id}'


def extract(body):
    """Full page bytes -> the three tables the dataset uses, as HTML strings (None when absent)."""
    doc = BeautifulSoup(body.decode('utf-8'), 'html.parser')
    info = doc.select_one('table#info')
    edu = next((t for t in doc.find_all('table')
                if any(c.get_text(strip=True) == '1.1' for row in t.find_all('tr') for c in row.find_all('td', limit=1))), None)
    result = doc.select_one('table#result')
    return {k: None if v is None else str(v) for k, v in dict(info=info, edu=edu, result=result).items()}


def record(registry_id, edition, fetch):
    url = PAGE.format(edition=edition, id=registry_id)
    row = dict(registryId=registry_id, edition=edition, url=url, fetchedAt=datetime.now(timezone.utc).isoformat(),
               status=None, bytes=0, sha256=None, info=None, edu=None, result=None)
    status, body = fetch(url)
    row['status'] = status
    if status == 200:
        row.update(bytes=len(body), sha256=hashlib.sha256(body).hexdigest(), **extract(body))
    return row


def http(url):
    request = Request(url, headers={'User-Agent': 'AdmitFlow-HistoryResearch/1.0', 'Accept': 'text/html'})
    try:
        response = urlopen(request, timeout=25)
    except HTTPError as error:
        return error.code, b''
    with response:
        if urlsplit(response.url).hostname != 'monitoring.miccedu.ru':
            raise ValueError('unexpected redirect')
        body = response.read(5*1024*1024 + 1)
    if len(body) > 5*1024*1024:
        raise ValueError('page too large')
    return response.status, body


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--pause', type=float, default=0.5)
    args = parser.parse_args(argv)
    heads = [r['registryId'] for r in json.loads(CATALOG.read_text(encoding='utf-8'))['institutions'] if not r['isBranch']]
    done = set()
    if args.output.exists():
        with gzip.open(args.output, 'rt', encoding='utf-8') as source:
            done = {(r['registryId'], r['edition']) for r in map(json.loads, source)}
    todo = [(i, e) for e in sorted(EDITIONS, reverse=True) for i in heads if (i, e) not in done]
    lock = threading.Lock()

    def run(item):
        row = record(*item, http)
        time.sleep(args.pause)
        with lock, gzip.open(args.output, 'at', encoding='utf-8') as sink:
            sink.write(json.dumps(row, ensure_ascii=False) + '\n')

    with ThreadPoolExecutor(max_workers=2) as pool:
        for count, _ in enumerate(pool.map(run, todo), 1):
            if count % 100 == 0:
                print(f'{count}/{len(todo)}', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
