from concurrent.futures import ThreadPoolExecutor, TimeoutError
from datetime import timedelta
import multiprocessing
import os
import threading

import pytest
from sqlalchemy.orm import Session

from app.admissions import PublishedSnapshot
from app.database import make_engine
from app.sources.publishing import publish
from app.sources.retention import cleanup_raw
from app.sources.storage import RawStore
from source_helpers import NOW, parsed, raw, registry, seed_source


def old(store,key):
    stamp=(NOW-timedelta(days=10)).timestamp()
    os.utime(store.root/key,(stamp,stamp))


def test_dry_run_age_and_all_referenced_history(source_engine,tmp_path):
    seed_source(source_engine)
    store=RawStore(tmp_path/'raw')
    referenced=raw()
    publish(source_engine,'source-1',parsed(),referenced,store,registry=registry(),allow_unattested=True)
    newer=raw(b'newer snapshot',NOW+timedelta(minutes=1))
    publish(source_engine,'source-1',parsed(),newer,store,registry=registry(),allow_unattested=True)
    orphan=store.put(b'orphaned synthetic data')
    recent=store.put(b'recent')
    old(store,referenced.payload_hash)
    old(store,newer.payload_hash)
    old(store,orphan)
    result=cleanup_raw(source_engine,store,now=NOW)
    assert result['candidates']==1 and result['deleted']==0
    assert store.read(orphan)
    result=cleanup_raw(source_engine,store,now=NOW,apply=True)
    assert result['deleted']==1
    assert store.read(referenced.payload_hash) and store.read(recent)
    assert store.read(newer.payload_hash)
    assert not (store.root/orphan).exists()


def test_database_error_never_deletes_files(tmp_path):
    engine=make_engine(f"sqlite:///{tmp_path/'empty.db'}")
    store=RawStore(tmp_path/'raw')
    key=store.put(b'orphan')
    old(store,key)
    with pytest.raises(Exception):
        cleanup_raw(engine,store,now=NOW,apply=True)
    assert store.read(key)==b'orphan'
    engine.dispose()


def test_gc_waits_until_publication_commit(source_engine,tmp_path,monkeypatch):
    seed_source(source_engine)
    store=RawStore(tmp_path/'raw')
    store.put(raw().body)
    old(store,raw().payload_hash)
    entered,release=threading.Event(),threading.Event()
    original=Session.commit
    def paused(db):
        # Fact-history queries can flush and release the pointer object before
        # commit. Read the uncommitted pointer in this transaction explicitly.
        if db.get(PublishedSnapshot,'source-1') is not None:
            entered.set()
            assert release.wait(3)
        return original(db)
    monkeypatch.setattr(Session,'commit',paused)
    with ThreadPoolExecutor(max_workers=2) as pool:
        publisher=pool.submit(publish,source_engine,'source-1',parsed(),raw(),store,registry=registry(),allow_unattested=True)
        assert entered.wait(3)
        cleaner=pool.submit(cleanup_raw,source_engine,RawStore(store.root),now=NOW,apply=True)
        try:
            with pytest.raises(TimeoutError):
                cleaner.result(timeout=0.05)
        finally:
            release.set()
        publisher.result()
        assert cleaner.result()['deleted']==0
    assert store.read(raw().payload_hash)


def child_put(folder,send):
    send.send('started')
    RawStore(folder).put(b'process data')
    send.send('finished')
    send.close()


def test_store_lock_is_shared_between_processes(tmp_path):
    store=RawStore(tmp_path)
    ctx=multiprocessing.get_context('spawn')
    receive,send=ctx.Pipe(duplex=False)
    process=ctx.Process(target=child_put,args=(str(tmp_path),send))
    try:
        with store.locked():
            process.start()
            send.close()
            assert receive.poll(5) and receive.recv()=='started'
            assert not receive.poll(0.1)
        assert receive.poll(5) and receive.recv()=='finished'
        process.join(5)
        assert process.exitcode==0
    finally:
        if process.is_alive():
            process.terminate()
            process.join(2)
        receive.close()
        send.close()
