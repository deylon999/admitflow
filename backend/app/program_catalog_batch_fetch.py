"""Give programme captures a wall-clock deadline, including system DNS."""
from datetime import datetime
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import time

from .sources.fetcher import FetchError, Fetcher, FetchResult


def _download(url, policy, folder):
    for name in ('DATABASE_URL', 'SOURCE_IDENTITY_KEY'):
        os.environ.pop(name, None)
    try:
        result = Fetcher(policy).fetch(url)
    except FetchError as error:
        metadata = {'error': error.code, 'retryAfter': error.retry_after}
    else:
        (folder/'body').write_bytes(result.body)
        metadata = {'url': result.url, 'contentType': result.content_type, 'sha256': result.payload_hash,
                    'fetchedAt': result.fetched_at.isoformat(), 'charset': result.charset}
    (folder/'result').write_text(json.dumps(metadata), encoding='utf-8')


def bounded_fetch(url, policy, *, timeout=30):
    # The parent reads the private exchange only after the child has exited.
    # A stalled resolver or partially written body cannot block the parent.
    with TemporaryDirectory(prefix='admitflow-programme-fetch-') as directory:
        folder = Path(directory)
        context = multiprocessing.get_context('spawn')
        process = context.Process(target=_download, args=(url, policy, folder), daemon=True)
        deadline = time.monotonic() + timeout
        try:
            process.start()
            process.join(max(0, deadline-time.monotonic()))
            if process.is_alive():
                raise FetchError('timeout', retry_after=60)
            if process.exitcode != 0:
                raise FetchError('network_error', retry_after=60)
            return _read_result(folder, policy)
        finally:
            if process.pid is not None:
                if process.is_alive():
                    process.kill()
                    process.join(2)
                if not process.is_alive():
                    process.close()


def _read_result(folder, policy):
    try:
        with (folder/'result').open('rb') as file:
            envelope = file.read(8193)
        if len(envelope) > 8192:
            raise ValueError()
        metadata = json.loads(envelope)
        if 'error' in metadata:
            raise FetchError(metadata['error'], retry_after=metadata['retryAfter'])
        with (folder/'body').open('rb') as file:
            body = file.read(policy.max_bytes+1)
        if (not 1 <= len(body) <= policy.max_bytes or metadata['contentType'] not in policy.content_types
                or hashlib.sha256(body).hexdigest() != metadata['sha256']):
            raise ValueError()
        return FetchResult(metadata['url'], body, metadata['contentType'], metadata['sha256'],
                           datetime.fromisoformat(metadata['fetchedAt']), metadata['charset'])
    except (OSError, ValueError, TypeError, KeyError):
        raise FetchError('invalid_headers') from None
