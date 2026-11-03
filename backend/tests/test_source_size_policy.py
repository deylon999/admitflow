from dataclasses import replace
import hashlib
import json

import pytest

from app.sources.fetcher import FetchError, Fetcher, FetchPolicy, RawResponse
from app.sources.registry import Registry
from app.sources.storage import RawStore, StorageError
from app.worker import _read_fetch_result, run_once
from app.jobs import enqueue
from source_helpers import BINDING, NOW, parsed, raw, registry, seed_source

SGU_SIZE = 5_851_174


def test_default_five_mib_refuses_observed_sgu_size_but_declared_eight_accepts():
    body = b'x' * SGU_SIZE  # Synthetic size boundary, not an invented original document.
    class Reader:
        def read(self, *_):
            return RawResponse(200, {'content-type':'text/plain','content-length':str(len(body))}, body)
    with pytest.raises(FetchError,match='response_too_large'):
        Fetcher(FetchPolicy(frozenset({'example.org'})),reader=Reader(),resolver=lambda _:['93.184.216.34']).fetch(BINDING.url)
    result = Fetcher(FetchPolicy(frozenset({'example.org'}),max_bytes=8*1024*1024),reader=Reader(),resolver=lambda _:['93.184.216.34']).fetch(BINDING.url)
    assert result.body == body
    with pytest.raises(ValueError):
        FetchPolicy(frozenset({'example.org'}),max_bytes=8*1024*1024+1)


def test_subprocess_envelope_obeys_selected_limit_before_reading(tmp_path):
    body = b'x' * SGU_SIZE
    (tmp_path/'payload.bin').write_bytes(body)
    (tmp_path/'result.json').write_text(json.dumps(dict(state='ok',url=BINDING.url,content_type='text/plain',
        payload_hash=hashlib.sha256(body).hexdigest(),fetched_at=NOW.isoformat(),charset='utf-8',byte_count=len(body))))
    with pytest.raises(FetchError,match='invalid_headers'):
        _read_fetch_result(tmp_path)
    assert _read_fetch_result(tmp_path,max_bytes=8*1024*1024).body == body
    (tmp_path/'payload.bin').write_bytes(body+b'x')
    with pytest.raises(FetchError,match='invalid_headers'):
        _read_fetch_result(tmp_path,max_bytes=8*1024*1024)


def test_raw_absolute_cap_and_worker_forwarding(source_engine,tmp_path):
    store=RawStore(tmp_path/'raw')
    body=b'x'*(8*1024*1024)
    digest=store.put(body)
    assert store.read(digest)==body
    with pytest.raises(StorageError,match='raw_size_invalid'):
        store.put(body+b'x')
    seed_source(source_engine)
    enqueue(source_engine,'source-1',now=NOW)
    adapter=replace(registry()._adapters['synthetic-v1'],max_bytes=8*1024*1024)
    def fetch(binding,domains,*,max_bytes):
        assert binding==BINDING and max_bytes==8*1024*1024
        return raw(b'x'*SGU_SIZE)
    assert run_once(source_engine,store,registry=Registry((adapter,)),allow_unattested=True,now=lambda:NOW,fetch=fetch)['state']=='success'


def test_large_referenced_raw_survives_backup_verify_and_restore(client,application,tmp_path):
    from app.backup import create_backup, restore_backup, verify_backup
    from app.sources.publishing import publish
    engine=application.state.engine
    seed_source(engine)
    store=RawStore(tmp_path/'raw')
    response=raw(b'x'*SGU_SIZE)
    declared=Registry((replace(registry()._adapters['synthetic-v1'],max_bytes=8*1024*1024),))
    publish(engine,'source-1',parsed(),response,store,registry=declared,allow_unattested=True)
    backup=create_backup(engine,store,tmp_path/'backups')
    assert verify_backup(backup).raw_hashes == [response.payload_hash]
    restored=restore_backup(backup,tmp_path/'new-recovery')
    assert RawStore(restored/'raw').read(response.payload_hash)==response.body
