from datetime import timedelta
from dataclasses import replace
import hashlib
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import event,func,select
from sqlalchemy.orm import Session
from app.admissions import Assessment,ChangeEvent,SourceSnapshot
from app.scenario_storage import enable_scenarios
from app.sources.publishing import publish
from app.sources.storage import RawStore
from test_api import HEADERS,start
from test_source_lookup import lookup_context
from test_sgu_adapter import BINDING
from test_scenario_storage import changed_consent
from test_subscriptions import confirm


def setup_change(context,tmp_path):
    client,app=context;start(client);enable_scenarios(app.state.engine,BINDING.source_id,registry=app.state.source_registry)
    saved=client.post('/api/v1/subscriptions',json=confirm(client,20),headers=HEADERS).json()
    assert client.get('/api/v1/changes').json()['items']==[]
    parsed,raw=changed_consent(app,tmp_path)
    for _ in range(2):publish(app.state.engine,BINDING.source_id,parsed,raw,RawStore(tmp_path/'raw'),registry=app.state.source_registry)
    return client,app,saved,raw


def test_changefeed_is_private_deduplicated_and_seen_is_idempotent(lookup_context,tmp_path):
    client,app,saved,raw=setup_change(lookup_context,tmp_path)
    page=client.get('/api/v1/changes').json();assert page['total']==page['unreadCount']==len(page['items'])==1
    item=page['items'][0];assert item['seenAt'] is None and item['scenario']['previousId'] and item['scenario']['changes']
    path=f"/api/v1/subscriptions/{saved['id']}/scenarios/"
    assert client.get(path+item['scenario']['id']).json()==item['scenario']
    assert client.get(path+item['scenario']['previousId']).json()['changes']==[]
    with TestClient(app) as other:
        start(other);assert other.get('/api/v1/changes').json()['total']==0
        assert other.post(f"/api/v1/changes/{item['id']}/seen",headers=HEADERS).status_code==404
        assert other.get(path+item['scenario']['id']).status_code==404
        assert other.get('/api/v1/changes',params={'before':item['id']}).status_code==400
    assert client.post(f"/api/v1/changes/{item['id']}/seen").status_code==403
    seen=client.post(f"/api/v1/changes/{item['id']}/seen",headers=HEADERS).json()
    assert seen['seenAt'] and client.post(f"/api/v1/changes/{item['id']}/seen",headers=HEADERS).json()==seen
    assert client.get('/api/v1/changes',params={'unread':True}).json()['items']==[]
    assert client.get('/api/v1/changes').json()['unreadCount']==0
    # Template-only publication creates a version, but no semantic event.
    body=b'<!-- synthetic template only -->\n'+raw.body
    newer=replace(raw,body=body,payload_hash=hashlib.sha256(body).hexdigest(),fetched_at=raw.fetched_at+timedelta(minutes=1))
    publish(app.state.engine,BINDING.source_id,app.state.source_registry.resolve(BINDING).parse(newer,BINDING),newer,RawStore(tmp_path/'raw'),registry=app.state.source_registry)
    assert client.get('/api/v1/changes').json()['total']==1
    assert client.delete(f"/api/v1/subscriptions/{saved['id']}",headers=HEADERS).status_code==204
    with Session(app.state.engine) as db:assert db.scalar(select(func.count()).select_from(ChangeEvent))==0


def test_changefeed_same_clock_cursor_survives_seen_and_new_events(lookup_context,tmp_path):
    client,app,saved,raw=setup_change(lookup_context,tmp_path)
    # Persist several independent versions at the same processing timestamp.
    with Session(app.state.engine) as db:
        original=db.scalar(select(ChangeEvent));a=db.get(Assessment,original.assessment_id)
        for number in range(4):
            clone=Assessment(subscription_id=a.subscription_id,group_id=a.group_id,snapshot_id=a.snapshot_id,rules_version=f'cursor-fixture-{number}',assessed_at=a.assessed_at,state=a.state,facts=a.facts,assumptions=a.assumptions)
            db.add(clone);db.flush();db.add(ChangeEvent(assessment_id=clone.id,created_at=original.created_at))
        db.commit()
    page=client.get('/api/v1/changes',params={'limit':2,'unread':True}).json();cursor=page['nextCursor'];assert cursor and page['total']==5
    for item in page['items']:client.post(f"/api/v1/changes/{item['id']}/seen",headers=HEADERS)
    rest=client.get('/api/v1/changes',params={'before':cursor,'unread':True}).json()
    assert len(rest['items'])==3 and not ({i['id'] for i in rest['items']}&{i['id'] for i in page['items']})
    assert client.delete('/api/v1/session',headers=HEADERS).status_code==204
    with Session(app.state.engine) as db:assert db.scalar(select(func.count()).select_from(ChangeEvent))==0


def test_change_insert_failure_rolls_back_snapshot_and_scenarios(lookup_context,tmp_path):
    client,app=lookup_context;start(client);enable_scenarios(app.state.engine,BINDING.source_id,registry=app.state.source_registry)
    saved=client.post('/api/v1/subscriptions',json=confirm(client,20),headers=HEADERS).json();path=f"/api/v1/subscriptions/{saved['id']}/scenario";before=client.get(path).json()
    def fail(*_):raise RuntimeError('Injected event insert failure')
    event.listen(ChangeEvent,'before_insert',fail)
    try:
        parsed,raw=changed_consent(app,tmp_path)
        with pytest.raises(RuntimeError,match='Injected'):publish(app.state.engine,BINDING.source_id,parsed,raw,RawStore(tmp_path/'raw'),registry=app.state.source_registry)
    finally:event.remove(ChangeEvent,'before_insert',fail)
    assert client.get(path).json()==before and client.get('/api/v1/changes').json()['items']==[]
    with Session(app.state.engine) as db:assert db.scalar(select(func.count()).select_from(SourceSnapshot))==1
