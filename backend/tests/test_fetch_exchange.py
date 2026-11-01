import hashlib
import json
from pathlib import Path
import time

import pytest

from app.sources.fetcher import FetchError
from app.worker import bounded_fetch
from source_helpers import BINDING


def partial_child(folder,*_):
    Path(folder,'payload.bin').write_bytes(b'partial')
    Path(folder,'result.writing').write_bytes(b'{"state":"ok"')
    Path(folder).with_suffix('.started').write_text('started')
    time.sleep(10)


def valid_child(folder,*_):
    body=b'x'*(1024*1024)
    Path(folder,'payload.bin').write_bytes(body)
    Path(folder,'result.json').write_text(json.dumps(dict(state='ok',url=BINDING.url,content_type='text/plain',payload_hash=hashlib.sha256(body).hexdigest(),fetched_at='2026-11-01T00:00:00Z',charset='utf-8',byte_count=len(body))))


def malformed_child(folder,*_):
    Path(folder,'result.json').write_text('{"state":"ok"}')


def test_partial_exchange_times_out_and_cleans_private_files(tmp_path,monkeypatch):
    folder=tmp_path/'private-fetch'
    folder.mkdir()
    monkeypatch.setattr('app.worker.tempfile.mkdtemp',lambda **_:str(folder))
    monkeypatch.setattr('app.worker._fetch_child',partial_child)
    start=time.monotonic()
    with pytest.raises(FetchError,match='timeout'):
        bounded_fetch(BINDING,frozenset({'example.org'}),timeout=2)
    assert folder.with_suffix('.started').read_text()=='started'
    folder.with_suffix('.started').unlink()
    assert time.monotonic()-start<5 and not folder.exists()


def test_large_completed_exchange_is_verified_and_malformed_result_rejected(tmp_path,monkeypatch):
    for child,valid in [(valid_child,True),(malformed_child,False)]:
        folder=tmp_path/child.__name__
        folder.mkdir()
        monkeypatch.setattr('app.worker.tempfile.mkdtemp',lambda **_:str(folder))
        monkeypatch.setattr('app.worker._fetch_child',child)
        if valid:
            result=bounded_fetch(BINDING,frozenset({'example.org'}))
            assert len(result.body)==1024*1024
        else:
            with pytest.raises(FetchError,match='invalid_headers'):
                bounded_fetch(BINDING,frozenset({'example.org'}))
        assert not folder.exists()


def test_cleanup_failure_does_not_mask_fetch_outcome_or_reveal_paths(tmp_path,monkeypatch,caplog):
    for child,valid in [(valid_child,True),(malformed_child,False)]:
        folder=tmp_path/child.__name__
        folder.mkdir()
        original=Path.unlink
        def denied(path,*args,**kwargs):
            if path==folder/'payload.bin': raise PermissionError('private path credential')
            return original(path,*args,**kwargs)
        with monkeypatch.context() as patch:
            patch.setattr('app.worker.tempfile.mkdtemp',lambda **_:str(folder))
            patch.setattr('app.worker._fetch_child',child)
            patch.setattr(Path,'unlink',denied)
            if valid:
                assert len(bounded_fetch(BINDING,frozenset({'example.org'})).body)==1024*1024
            else:
                with pytest.raises(FetchError,match='invalid_headers'):
                    bounded_fetch(BINDING,frozenset({'example.org'}))
        assert not (folder/'result.json').exists()
        assert 'fetch_cleanup_incomplete' in caplog.text and 'private path' not in caplog.text
        (folder/'payload.bin').unlink(missing_ok=True)
        if folder.exists(): folder.rmdir()
