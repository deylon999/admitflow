from concurrent.futures import ThreadPoolExecutor
import hashlib

import pytest

from app.sources.storage import RawStore, StorageError


def test_atomic_concurrent_repeat_and_integrity(tmp_path):
    store = RawStore(tmp_path/'raw')
    body = b'synthetic source payload'
    with ThreadPoolExecutor(max_workers=8) as pool:
        keys = list(pool.map(store.put,[body]*24))
    assert len(set(keys)) == 1
    assert [p.name for p in store.root.iterdir()] == [keys[0]]
    assert store.read(keys[0]) == body
    (store.root/keys[0]).write_bytes(b'corrupt')
    with pytest.raises(StorageError,match='raw_hash_mismatch'):
        store.read(keys[0])
    with pytest.raises(StorageError,match='raw_hash_mismatch'):
        store.put(body)


def test_invalid_path_hash_and_size_do_not_write(tmp_path):
    store = RawStore(tmp_path,max_bytes=10)
    for path in ['../outside','A'*64,'x'*64,'/absolute']:
        with pytest.raises(StorageError,match='invalid_digest'):
            store.read(path)
    for body in [b'',b'x'*11]:
        with pytest.raises(StorageError,match='raw_size_invalid'):
            store.put(body)
    with pytest.raises(StorageError,match='raw_hash_mismatch'):
        store.put(b'ok',expected_hash='0'*64)
    with pytest.raises(StorageError,match='raw_unavailable'):
        store.read('0'*64)
    assert list(tmp_path.iterdir()) == []


def test_read_size_limit_applies_to_files_already_on_disk(tmp_path):
    store = RawStore(tmp_path,max_bytes=10)
    body=b'x'*11
    key=hashlib.sha256(body).hexdigest()
    (tmp_path/key).write_bytes(body)
    with pytest.raises(StorageError,match='raw_size_invalid'):
        store.read(key)
