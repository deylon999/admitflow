from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.admissions import CandidateEntry, PublishedSnapshot, Source, SourceSnapshot
from app.sources.publishing import publish
from app.sources.storage import RawStore
from app.sources.validation import Quarantined
from source_helpers import NOW, parsed, raw, registry, seed_source


def publish_sample(engine,store,value=None,response=None,**options):
    return publish(engine,'source-1',value or parsed(),response or raw(),store,registry=registry('synthetic-v1','synthetic-v2'),allow_unattested=True,**options)


def test_atomic_repeat_concurrency_and_new_parser_version(source_engine,tmp_path):
    seed_source(source_engine)
    store=RawStore(tmp_path/'raw')
    with ThreadPoolExecutor(max_workers=4) as pool:
        ids=list(pool.map(lambda _:publish_sample(source_engine,store),range(8)))
    assert len(set(ids)) == 1
    with Session(source_engine) as db:
        assert db.scalar(select(func.count()).select_from(SourceSnapshot)) == 1
        assert db.scalar(select(func.count()).select_from(CandidateEntry)) == 3
        db.get(Source,'source-1').adapter_version='synthetic-v2'
        db.commit()
    second=publish_sample(source_engine,store,parsed(version='synthetic-v2'))
    assert second != ids[0]
    with Session(source_engine) as db:
        assert db.get(PublishedSnapshot,'source-1').snapshot_id == second
        assert db.get(SourceSnapshot,ids[0]).adapter_version == 'synthetic-v1'
        assert db.scalar(select(func.count()).select_from(SourceSnapshot)) == 2


def test_rejected_or_failed_write_preserves_latest_and_history(source_engine,tmp_path,monkeypatch):
    seed_source(source_engine)
    store=RawStore(tmp_path/'raw')
    first=publish_sample(source_engine,store)
    with pytest.raises(Quarantined,match='incomplete_list'):
        publish_sample(source_engine,store,parsed().model_copy(update={'complete':False}),raw(b'broken',NOW+timedelta(minutes=1)))
    original=Session.flush
    def fail_rows(db,*args,**kwargs):
        if any(isinstance(row,CandidateEntry) for row in db.new):
            raise RuntimeError('synthetic failure')
        return original(db,*args,**kwargs)
    with monkeypatch.context() as patch:
        patch.setattr(Session,'flush',fail_rows)
        with pytest.raises(RuntimeError,match='synthetic failure'):
            publish_sample(source_engine,store,response=raw(b'new',NOW+timedelta(minutes=2)))
    with Session(source_engine) as db:
        assert db.get(PublishedSnapshot,'source-1').snapshot_id == first
        assert db.scalar(select(func.count()).select_from(SourceSnapshot)) == 1
        assert db.scalar(select(func.count()).select_from(CandidateEntry)) == 3
        assert db.get(Source,'source-1').last_error_code is None


def test_reinterpreting_same_raw_with_same_version_is_quarantined(source_engine,tmp_path):
    seed_source(source_engine)
    store=RawStore(tmp_path/'raw')
    publish_sample(source_engine,store)
    with pytest.raises(Quarantined,match='nondeterministic_parser'):
        publish_sample(source_engine,store,parsed().model_copy(update={'seats':11}))
