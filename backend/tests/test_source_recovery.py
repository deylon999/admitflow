from dataclasses import replace
from datetime import timedelta
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.admissions import PublishedSnapshot, Source
from app.jobs import SourceCheck, enqueue
from app.worker import run_once
from app.sources.storage import RawStore
from test_api import HEADERS,start
from test_source_lookup import lookup_context
from test_sgu_adapter import BINDING,response
from test_subscriptions import confirm


def test_real_format_failure_quarantine_recovery_retains_history(lookup_context,tmp_path):
    client,app=lookup_context;start(client)
    saved=client.post('/api/v1/subscriptions',json=confirm(client),headers=HEADERS).json()
    initial=client.get('/api/v1/subscriptions').json()[0]
    raw=response();registry=app.state.source_registry;store=RawStore(tmp_path/'raw')
    for offset,body,expected in [(901,b'<html>Login required</html>','failed'),(1802,raw.body,'success')]:
        at=raw.fetched_at+timedelta(seconds=offset)
        assert enqueue(app.state.engine,BINDING.source_id,now=at)
        fetched=response(body);fetched=replace(fetched,fetched_at=at)
        assert run_once(app.state.engine,store,registry=registry,now=lambda:at,fetch=lambda *_,**__:fetched)['state']==expected
        current=client.get('/api/v1/subscriptions').json()[0]
        assert current['group']['snapshotId']==initial['group']['snapshotId']
        assert current['group']['fetchedAt']==initial['group']['fetchedAt']
        assert current['candidate']==initial['candidate']
        assert current['group']['sourceUpdatedAt'] is None
        assert current['group']['sourceState']==('source_error' if expected=='failed' else 'archived')
    # Recovery clears current error, not the historical failed check.
    checks=client.get(f'/api/v1/sources/{BINDING.source_id}/checks')
    assert checks.status_code==200
    assert [x['outcome'] for x in checks.json()]==['success','failed']
    assert checks.json()[1]['errorCode']=='invalid_format'
    assert 'FIXTURE-' not in checks.text and 'candidateKey' not in checks.text
    assert client.get(f"/api/v1/subscriptions/{saved['id']}/history").json()['total']==1
    with Session(app.state.engine) as db:
        assert db.get(Source,BINDING.source_id).last_error_code is None
        assert len(db.scalars(select(SourceCheck)).all())==2
    assert client.get('/api/v1/sources/missing/checks').status_code==404


def test_synthetic_quality_quarantine_then_recovery_keeps_both_outcomes(lookup_context,tmp_path):
    from app.sources.registry import Registry
    client,app=lookup_context;raw=response();adapter=app.state.source_registry.resolve(BINDING)
    parsed=adapter.parse(raw,BINDING)
    invalid=parsed.model_copy(update={'entries':(parsed.entries[0],)+parsed.entries[:-1]})
    injected=Registry((replace(adapter,parse=lambda *_:invalid),))
    for offset,registry,expected in [(901,injected,'failed'),(1802,app.state.source_registry,'success')]:
        at=raw.fetched_at+timedelta(seconds=offset);enqueue(app.state.engine,BINDING.source_id,now=at)
        fetched=replace(raw,fetched_at=at)
        assert run_once(app.state.engine,RawStore(tmp_path/'raw'),registry=registry,now=lambda:at,fetch=lambda *_,**__:fetched)['state']==expected
        state=client.get(f'/api/v1/sources/{BINDING.source_id}/status').json()
        assert state['state']==('quarantined' if expected=='failed' else 'archived')
        assert state['fetchedAt']==raw.fetched_at.isoformat().replace('+00:00','Z')
    checks=client.get(f'/api/v1/sources/{BINDING.source_id}/checks').json()
    assert checks[1]['errorCode']=='duplicate_candidate' and checks[0]['outcome']=='success'
