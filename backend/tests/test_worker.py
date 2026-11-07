from dataclasses import replace
from datetime import timedelta
import time

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.admissions import PublishedSnapshot, Source, SourceSnapshot
from app.jobs import SourceJob, claim, disable, enqueue
from app.sources.cli import main as cli_main, operate
from app.sources.fetcher import FetchError
from app.sources.registry import Adapter, Registry
from app.sources.storage import RawStore
from app.worker import bounded_fetch, main as worker_main, run_once
from source_helpers import BINDING, NOW, parsed, raw, registry, seed_source


def test_synthetic_worker_success_then_quarantine_preserves_latest(source_engine,tmp_path):
    seed_source(source_engine)
    enqueue(source_engine,'source-1',now=NOW,interval_seconds=60)
    store=RawStore(tmp_path/'raw')
    run=lambda **options:run_once(source_engine,store,allow_unattested=True,now=lambda:NOW,**options)
    assert run(registry=registry(),fetch=lambda *_:raw())['state']=='success'
    with Session(source_engine) as db:
        first=db.get(PublishedSnapshot,'source-1').snapshot_id
        assert db.get(SourceJob,'source-1').state=='idle'
    bad=Registry((Adapter('synthetic-v1',frozenset({'example.org'}),lambda *_:parsed().model_copy(update={'complete':False})),))
    result=run_once(source_engine,store,registry=bad,allow_unattested=True,now=lambda:NOW+timedelta(minutes=1),fetch=lambda *_:raw(b'incomplete',NOW+timedelta(minutes=1)))
    assert result['state']=='failed'
    with Session(source_engine) as db:
        assert db.get(PublishedSnapshot,'source-1').snapshot_id==first
        assert db.get(Source,'source-1').last_error_code=='incomplete_list'
        assert db.get(SourceJob,'source-1').state=='failed'


def test_worker_lost_lease_cannot_publish(source_engine,tmp_path):
    seed_source(source_engine)
    enqueue(source_engine,'source-1',now=NOW)
    def delayed_fetch(*_):
        assert claim(source_engine,now=NOW+timedelta(seconds=121)) is not None
        return raw()
    result=run_once(source_engine,RawStore(tmp_path/'raw'),registry=registry(),allow_unattested=True,now=lambda:NOW,fetch=delayed_fetch)
    assert result['state']=='lost_lease'
    with Session(source_engine) as db:
        assert db.scalar(select(func.count()).select_from(SourceSnapshot))==0
        assert db.get(Source,'source-1').last_error_code is None


def test_disable_during_fetch_prevents_publication(source_engine,tmp_path):
    seed_source(source_engine)
    enqueue(source_engine,'source-1',now=NOW)
    def disabled_fetch(*_):
        disable(source_engine,'source-1',now=NOW)
        return raw()
    result=run_once(source_engine,RawStore(tmp_path/'raw'),registry=registry(),allow_unattested=True,now=lambda:NOW,fetch=disabled_fetch)
    assert result['state']=='lost_lease'
    with Session(source_engine) as db:
        assert db.get(PublishedSnapshot,'source-1') is None


def test_transient_fetch_retries_and_production_registry_never_fetches_unknown(source_engine,tmp_path):
    seed_source(source_engine)
    enqueue(source_engine,'source-1',now=NOW,interval_seconds=60)
    def unavailable(*_):
        raise FetchError('rate_limited',retry_after=300)
    result=run_once(source_engine,RawStore(tmp_path/'raw'),registry=registry(),allow_unattested=True,now=lambda:NOW,fetch=unavailable)
    assert result['state']=='failed'
    with Session(source_engine) as db:
        assert db.get(SourceJob,'source-1').state=='queued'
        assert db.get(SourceJob,'source-1').last_error_code=='rate_limited'
    def must_not_fetch(*_):
        raise AssertionError('unknown adapter reached fetch')
    result=run_once(source_engine,RawStore(tmp_path/'raw'),now=lambda:NOW+timedelta(seconds=300),fetch=must_not_fetch)
    assert result['state']=='failed'
    with Session(source_engine) as db:
        assert db.get(SourceJob,'source-1').last_error_code=='adapter_unavailable'


def stall_child(*_):
    time.sleep(5)


def test_fetch_subprocess_has_global_deadline_and_safe_error(monkeypatch):
    with pytest.raises(FetchError,match='invalid_url'):
        bounded_fetch(replace(BINDING,url='http://example.org'),frozenset({'example.org'}))
    monkeypatch.setattr('app.worker._fetch_child',stall_child)
    start=time.monotonic()
    with pytest.raises(FetchError,match='timeout'):
        bounded_fetch(BINDING,frozenset({'example.org'}),timeout=0.15)
    assert time.monotonic()-start<4


def test_operator_cli_and_worker_cli_do_not_enable_unattested_sources(source_engine,tmp_path,monkeypatch,capsys):
    seed_source(source_engine)
    monkeypatch.setenv('DATABASE_URL',str(source_engine.url))
    monkeypatch.setenv('RAW_STORE_PATH',str(tmp_path/'raw'))
    assert cli_main(['list'])==0
    assert 'source-1' in capsys.readouterr().out
    assert cli_main(['enqueue','source-1'])==1
    assert 'unattested' not in capsys.readouterr().out  # No adapter exists in production.
    assert worker_main(['once'])==0
    assert 'idle' in capsys.readouterr().out
    status=operate(source_engine,'status','source-1')
    assert status['job'] is None and status['assessmentAvailable'] is False
    assert cli_main(['disable','source-1'])==0
    assert 'false' in capsys.readouterr().out


def test_crash_after_publication_replays_without_second_snapshot(source_engine,tmp_path,monkeypatch):
    seed_source(source_engine)
    enqueue(source_engine,'source-1',now=NOW)
    store=RawStore(tmp_path/'raw')
    def crash(*args,**kwargs):
        raise SystemExit('simulated process death')
    with monkeypatch.context() as patch:
        patch.setattr('app.worker.complete',crash)
        with pytest.raises(SystemExit):
            run_once(source_engine,store,registry=registry(),allow_unattested=True,now=lambda:NOW,fetch=lambda *_:raw())
    later=NOW+timedelta(seconds=121)
    assert run_once(source_engine,store,registry=registry(),allow_unattested=True,now=lambda:later,fetch=lambda *_:raw(at=later))['state']=='success'
    with Session(source_engine) as db:
        assert db.scalar(select(func.count()).select_from(SourceSnapshot))==1
        assert db.get(SourceJob,'source-1').state=='idle'


def test_parser_exception_text_is_not_saved_or_returned(source_engine,tmp_path):
    seed_source(source_engine)
    enqueue(source_engine,'source-1',now=NOW)
    def bad_parser(*_):
        raise ValueError('private candidate data must not leave parser')
    bad=Registry((Adapter('synthetic-v1',frozenset({'example.org'}),bad_parser),))
    result=run_once(source_engine,RawStore(tmp_path/'raw'),registry=bad,allow_unattested=True,now=lambda:NOW,fetch=lambda *_:raw())
    assert result=={'state':'failed','sourceId':'source-1'}
    with Session(source_engine) as db:
        assert db.get(Source,'source-1').last_error_code=='internal_error'
        assert db.get(SourceJob,'source-1').last_error_code=='internal_error'


def test_fetch_child_does_not_keep_private_settings(monkeypatch,tmp_path):
    import os
    from app.worker import _fetch_child
    monkeypatch.setenv('SOURCE_IDENTITY_KEY','private-key')
    monkeypatch.setenv('DATABASE_URL','postgresql://private')
    seen={}
    class Stop:
        def __init__(self,*_):pass
        def fetch(self,url):
            seen['key']=os.environ.get('SOURCE_IDENTITY_KEY');seen['db']=os.environ.get('DATABASE_URL')
            raise FetchError('timeout',retry_after=60)
    monkeypatch.setattr('app.worker.Fetcher',Stop)
    monkeypatch.setattr('app.worker.FetchPolicy',lambda **_:None)
    binding=type('B',(),{'url':'https://example.org/list'})
    _fetch_child(str(tmp_path),binding,frozenset({'example.org'}))
    assert seen=={'key':None,'db':None}


def test_worker_memory_limit_setting_is_validated(monkeypatch):
    from app.worker import limit_memory
    monkeypatch.setenv('WORKER_MEMORY_LIMIT_MB','1')
    with pytest.raises(RuntimeError):
        limit_memory()


def test_missing_resource_fails_only_at_worker_memory_setup(monkeypatch):
    import sys
    from app.worker import limit_memory
    monkeypatch.setitem(sys.modules, 'resource', None)
    monkeypatch.setenv('WORKER_MEMORY_LIMIT_MB', '2048')
    with pytest.raises(RuntimeError, match='run the worker in Docker'):
        limit_memory()
