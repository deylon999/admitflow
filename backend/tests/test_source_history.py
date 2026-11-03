from dataclasses import replace
from datetime import timedelta
import hashlib
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.admissions import Assessment, SourceSnapshot
from app.sources.publishing import publish
from app.sources.storage import RawStore
from test_api import HEADERS, start
from test_source_lookup import lookup_context
from test_sgu_adapter import BINDING, response
from test_subscriptions import confirm


def publish_version(app, tmp_path, index, *, same_time=False):
    raw = response(); body = f'<!-- explicitly synthetic history scenario {index} -->\n'.encode()+raw.body
    raw = replace(raw, body=body, payload_hash=hashlib.sha256(body).hexdigest(), fetched_at=raw.fetched_at+timedelta(minutes=0 if same_time else index))
    adapter = app.state.source_registry.resolve(BINDING)
    parsed = adapter.parse(raw, BINDING)
    return publish(app.state.engine, BINDING.source_id, parsed, raw, RawStore(tmp_path/'raw'), registry=app.state.source_registry)


def test_archive_history_is_immutable_paginated_private_and_idempotent(lookup_context, tmp_path):
    client, app = lookup_context; start(client)
    saved = client.post('/api/v1/subscriptions', json=confirm(client), headers=HEADERS).json()
    path = f"/api/v1/subscriptions/{saved['id']}/history"
    initial = client.get(path).json()['items'][0]
    for index in range(1, 5): publish_version(app, tmp_path, index, same_time=True)
    # Identical last payload is deduplicated, including its assessment.
    publish_version(app, tmp_path, 4, same_time=True)
    seen=[]; cursor=None
    while True:
        page=client.get(path, params={'limit':2, **({'before':cursor} if cursor else {})}).json()
        assert page['total']==5
        seen.extend(page['items']); cursor=page['nextCursor']
        if not cursor:break
    assert len(seen)==5 and len({x['id'] for x in seen})==5
    assert next(x for x in seen if x['id']==initial['id'])==initial
    assert all(x['group']['year']==2026 and x['group']['seats']==16 and x['candidate']['officialRank']==1 for x in seen)
    assert 'candidateKey' not in str(seen) and 'FIXTURE-' not in str(seen)
    assert client.get(path, params={'before':'foreign-cursor'}).status_code==400
    with TestClient(app) as other:
        start(other); assert other.get(path).status_code==404
    assert client.get(path, params={'limit':101}).status_code==422
    with Session(app.state.engine) as db:
        assert len(db.scalars(select(Assessment)).all())==5
        assert len(db.scalars(select(SourceSnapshot)).all())==5


def test_history_failure_rolls_back_publication_and_pointer(lookup_context,tmp_path,monkeypatch):
    from app.admissions import PublishedSnapshot
    client,app=lookup_context;start(client)
    client.post('/api/v1/subscriptions',json=confirm(client),headers=HEADERS)
    with Session(app.state.engine) as db: old=db.get(PublishedSnapshot,BINDING.source_id).snapshot_id
    def fail(*_):raise RuntimeError('synthetic history failure')
    monkeypatch.setattr('app.source_history.append_snapshot_facts',fail)
    import pytest
    with pytest.raises(RuntimeError,match='synthetic history failure'):publish_version(app,tmp_path,1)
    with Session(app.state.engine) as db:
        assert db.get(PublishedSnapshot,BINDING.source_id).snapshot_id==old
        assert len(db.scalars(select(Assessment)).all())==1
        assert len(db.scalars(select(SourceSnapshot)).all())==1


def test_synthetic_changed_facts_keep_the_confirmation_unchanged(lookup_context,tmp_path):
    from bs4 import BeautifulSoup
    client,app=lookup_context;start(client)
    saved=client.post('/api/v1/subscriptions',json=confirm(client),headers=HEADERS).json()
    path=f"/api/v1/subscriptions/{saved['id']}/history"
    original=client.get(path).json()['items'][0]
    raw=response();soup=BeautifulSoup(raw.body,'html.parser')
    cell=soup.find(string=lambda text:text and 'FIXTURE-000001' in text)
    row=cell.find_parent('tr');cells=row.find_all('td')
    # Derived fixture only: toggle explicit consent, not an observed source event.
    consent=row.find('td',attrs={'data-label':'Согласие на зачисление'})
    consent.clear();consent.append('Да')
    body=('<!-- synthetic consent change, not an observed source event -->\n'+str(soup)).encode()
    changed=replace(raw,body=body,payload_hash=hashlib.sha256(body).hexdigest(),fetched_at=raw.fetched_at+timedelta(minutes=1))
    parsed=app.state.source_registry.resolve(BINDING).parse(changed,BINDING)
    publish(app.state.engine,BINDING.source_id,parsed,changed,RawStore(tmp_path/'raw'),registry=app.state.source_registry)
    history=client.get(path).json()['items']
    assert len(history)==2 and history[0]['candidate']['consent'] is True
    assert history[1]==original and history[1]['candidate']['consent'] is False


def test_processing_time_is_separate_from_archive_fetch_and_retry_keeps_it(lookup_context,tmp_path,monkeypatch):
    from datetime import datetime,timezone
    client,app=lookup_context;start(client)
    saved=client.post('/api/v1/subscriptions',json=confirm(client),headers=HEADERS).json()
    processed=datetime(2026,11,4,0,0,0,tzinfo=timezone.utc)
    monkeypatch.setattr('app.source_history.assessment_clock',lambda:processed)
    publish_version(app,tmp_path,1)
    path=f"/api/v1/subscriptions/{saved['id']}/history"
    newest=client.get(path).json()['items'][0]
    assert newest['assessedAt']=='2026-11-04T00:00:00Z'
    assert newest['group']['fetchedAt']!='2026-11-04T00:00:00Z' and newest['group']['sourceUpdatedAt'] is None
    monkeypatch.setattr('app.source_history.assessment_clock',lambda:processed+timedelta(hours=1))
    publish_version(app,tmp_path,1)
    assert client.get(path).json()['items'][0]==newest
