"""T041: failed runs can be traced and a dead worker differs from a dead API."""
from datetime import timedelta
import json
import logging

from sqlalchemy.orm import Session

from app.jobs import SourceJob, clock, enqueue
from app.observability import WORKER_STALE_SECONDS, beat, system_status, trace_run, worker_status
from app.sources.fetcher import FetchError
from app.sources.storage import RawStore
from app.worker import run_once
from source_helpers import raw, registry, seed_source


def events(caplog):
    return [json.loads(record.message) for record in caplog.records if record.name=='admitflow.worker']


def test_success_and_failure_rebuild_the_chain_without_private_data(source_engine,tmp_path,caplog):
    seed_source(source_engine)
    store=RawStore(tmp_path/'raw')
    at=raw().fetched_at
    enqueue(source_engine,'source-1',now=at)
    with caplog.at_level(logging.INFO,logger='admitflow.worker'):
        assert run_once(source_engine,store,registry=registry(),allow_unattested=True,now=lambda:at,fetch=lambda *_,**__:raw())['state']=='success'
    finished=events(caplog)[-1]
    assert finished['event']=='source_run_finished' and finished['state']=='success' and finished['snapshotId']
    with Session(source_engine) as db:
        chain=trace_run(db,finished['runId'])
    assert chain['outcome']=='success' and chain['sourceId']=='source-1' and chain['snapshot']['id']==finished['snapshotId'] and chain['assessments']==0
    assert chain['snapshot']['rowCount']==3

    caplog.clear()
    later=at+timedelta(hours=1)
    with Session(source_engine) as db:
        db.get(SourceJob,'source-1').next_run_at=later
        db.commit()
    def broken(*_,**__):
        raise FetchError('timeout',retry_after=60)
    with caplog.at_level(logging.INFO,logger='admitflow.worker'):
        assert run_once(source_engine,store,registry=registry(),allow_unattested=True,now=lambda:later,fetch=broken)['state']=='failed'
    failed=events(caplog)[-1]
    assert failed['code']=='timeout' and failed['errorType']=='FetchError'
    with Session(source_engine) as db:
        chain=trace_run(db,failed['runId'])
        assert trace_run(db,'missing') is None
    assert chain['outcome']=='failed' and chain['errorCode']=='timeout'


def test_internal_exception_text_never_reaches_events(source_engine,tmp_path,caplog):
    seed_source(source_engine)
    at=raw().fetched_at
    enqueue(source_engine,'source-1',now=at)
    def private(*_,**__):
        raise RuntimeError('private code 123-456 https://user:pass@example.org')
    with caplog.at_level(logging.INFO,logger='admitflow.worker'):
        run_once(source_engine,RawStore(tmp_path/'raw'),registry=registry(),allow_unattested=True,now=lambda:at,fetch=private)
    assert 'private' not in caplog.text and '123-456' not in caplog.text
    assert events(caplog)[-1]['errorType']=='RuntimeError'


def test_worker_liveness_is_separate_and_ages_out(source_engine):
    now=clock()
    with Session(source_engine) as db:
        assert worker_status(db,now=now)['state']=='never_seen'
    beat(source_engine,'w1',now,'idle',now=now)
    with Session(source_engine) as db:
        assert worker_status(db,now=now)['state']=='alive'
        assert worker_status(db,now=now+timedelta(seconds=WORKER_STALE_SECONDS+1))['state']=='stale'


def test_old_heartbeats_are_pruned_on_new_worker(source_engine):
    from app.observability import WorkerHeartbeat
    now=clock()
    beat(source_engine,'old',now-timedelta(days=30),'idle',now=now-timedelta(days=30))
    beat(source_engine,'new',now,'started',now=now)
    with Session(source_engine) as db:
        assert db.get(WorkerHeartbeat,'old') is None and db.get(WorkerHeartbeat,'new')


def test_jobs_without_worker_are_degraded_but_empty_system_is_not(source_engine):
    seed_source(source_engine)
    now=clock()
    with Session(source_engine) as db:
        assert system_status(db,now=now,registry=registry())['worker']['state']=='never_seen'
    enqueue(source_engine,'source-1',now=now)
    with Session(source_engine) as db:
        status=system_status(db,now=now,registry=registry())
    assert status['status']=='degraded' and status['jobs']['byState']=={'queued':1}
    beat(source_engine,'w1',now,'idle',now=now)
    with Session(source_engine) as db:
        status=system_status(db,now=now,registry=registry())
        overdue=system_status(db,now=now+timedelta(minutes=11),registry=registry())
    assert status['status']=='ok' and status['sources']['total']==1
    assert overdue['status']=='degraded' and overdue['jobs']['overdue']==1


def test_status_endpoint_is_aggregate_and_health_stays_independent(client):
    response=client.get('/api/status')
    assert response.status_code==200
    assert set(response.json())=={'status','checkedAt','worker','sources','jobs'}
    assert client.get('/api/health').status_code==200
