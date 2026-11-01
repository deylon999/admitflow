from concurrent.futures import ThreadPoolExecutor
import time

import pytest

from app.sources.storage import RawStore, StorageError


def contender(folder):
    store=RawStore(folder)
    start=time.monotonic()
    try:
        with store.locked(timeout=0.03):
            return 'unexpected_success',time.monotonic()-start
    except StorageError as error:
        return error.code,time.monotonic()-start


def test_thread_contention_obeys_deadline_and_releases_after_timeout(tmp_path):
    store=RawStore(tmp_path)
    with ThreadPoolExecutor(max_workers=1) as pool:
        with store.locked():
            result=pool.submit(contender,tmp_path).result(timeout=1)
            assert result[0]=='raw_lock_timeout' and result[1]<0.5
        # A timed-out waiter cannot retain the thread lock or file descriptor.
        key=pool.submit(store.put,b'after timeout').result(timeout=1)
        assert store.read(key)==b'after timeout'


def test_nested_operations_and_invalid_deadlines(tmp_path):
    first,second=RawStore(tmp_path),RawStore(tmp_path)
    with first.locked(timeout=0):
        with second.locked(timeout=0):
            key=second.put(b'nested')
            assert first.read(key)==b'nested'
    for value in [-1,float('inf'),float('nan'),'forever']:
        with pytest.raises(ValueError,match='invalid_lock_timeout'):
            with first.locked(timeout=value):
                pass
