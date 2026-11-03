from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import timedelta
import hashlib

from fastapi.testclient import TestClient
from sqlalchemy import func,select
from sqlalchemy.orm import Session

from app.admissions import Assessment,Subscription
from app.database import OperationRecord
from app.sources.publishing import publish
from app.sources.storage import RawStore
from test_api import HEADERS,WATCH,start
from test_sgu_adapter import BINDING,response
from test_source_lookup import lookup_context


def confirm(client,index=1):
    result=client.post(f'/api/v1/sources/{BINDING.source_id}/lookup',json={'publicCode':f'FIXTURE-{index:06d}'},headers=HEADERS)
    assert result.status_code==200 and result.json()['found']
    return {'confirmationToken':result.json()['confirmationToken']}


def test_repeated_confirmation_saves_once_and_other_owner_cannot_use_it(lookup_context):
    client,app=lookup_context;start(client);body=confirm(client)
    with ThreadPoolExecutor(max_workers=6) as pool:
        responses=list(pool.map(lambda _:client.post('/api/v1/subscriptions',json=body,headers=HEADERS),range(12)))
    assert all(r.status_code==201 for r in responses) and len({r.json()['id'] for r in responses})==1
    records=client.get('/api/v1/subscriptions').json()
    assert len(records)==1 and records[0]['candidate']['officialRank']==1 and records[0]['group']['dataKind']=='archive'
    with TestClient(app) as other:
        start(other)
        assert other.post('/api/v1/subscriptions',json=body,headers=HEADERS).status_code==403
        assert other.get('/api/v1/subscriptions').json()==[]
    with Session(app.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(Subscription))==1
        assert db.scalar(select(func.count()).select_from(Assessment))==1
        assert db.scalar(select(func.count()).select_from(OperationRecord))==1
        assert db.scalar(select(Assessment)).state=='unsupported'


def test_manual_and_archive_share_twenty_limit_under_concurrent_writes(lookup_context):
    client,_=lookup_context;start(client)
    for _ in range(18):assert client.post('/api/v1/watches',json=WATCH,headers=HEADERS).status_code==201
    bodies=[confirm(client,index) for index in range(1,5)]
    with ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(lambda body:client.post('/api/v1/subscriptions',json=body,headers=HEADERS).status_code,bodies))
    assert results.count(201)==2 and results.count(409)==2
    budget=client.get('/api/v1/direction-budget').json()
    assert budget=={'limit':20,'total':20,'manualCount':18,'archiveCount':2}
    assert client.post('/api/v1/watches',json=WATCH,headers=HEADERS).status_code==409
    bundle=client.get('/api/v1/export').json();bundle['watches']=bundle['watches'][:1]
    assert client.post('/api/v1/import',json={'bundle':bundle},headers=HEADERS|{'Idempotency-Key':'combined-limit-import'}).status_code==409
    replay=next(body for body in bodies if client.post('/api/v1/subscriptions',json=body,headers=HEADERS).status_code==201)
    assert client.post('/api/v1/subscriptions',json=replay,headers=HEADERS).status_code==201


def test_stale_unconsumed_confirmation_refuses_but_successful_replay_ignores_expiry(lookup_context,tmp_path,monkeypatch):
    client,app=lookup_context;start(client);old=confirm(client)
    raw=response();body=b'<!-- synthetic template change for stale confirmation -->\n'+raw.body
    new=replace(raw,body=body,payload_hash=hashlib.sha256(body).hexdigest(),fetched_at=raw.fetched_at+timedelta(minutes=1))
    registry=app.state.source_registry
    publish(app.state.engine,BINDING.source_id,registry.resolve(BINDING).parse(new,BINDING),new,RawStore(tmp_path/'raw'),registry=registry)
    assert client.post('/api/v1/subscriptions',json=old,headers=HEADERS).status_code==409
    fresh=confirm(client);saved=client.post('/api/v1/subscriptions',json=fresh,headers=HEADERS)
    assert saved.status_code==201
    from app.main import utcnow
    now=utcnow();expired=confirm(client,2)
    monkeypatch.setattr('app.main.utcnow',lambda:now+timedelta(seconds=301))
    assert client.post('/api/v1/subscriptions',json=expired,headers=HEADERS).status_code==410
    replay=client.post('/api/v1/subscriptions',json=fresh,headers=HEADERS)
    assert replay.status_code==201 and replay.json()==saved.json()
    assert len(client.get('/api/v1/subscriptions').json())==1


def test_guest_reset_removes_subscription_assessment_and_operation_payload(lookup_context):
    client,app=lookup_context;start(client)
    assert client.post('/api/v1/subscriptions',json=confirm(client),headers=HEADERS).status_code==201
    assert client.delete('/api/v1/session',headers=HEADERS).status_code==204
    with Session(app.state.engine) as db:
        for model in (Subscription,Assessment,OperationRecord):assert db.scalar(select(func.count()).select_from(model))==0


def test_expiry_hides_private_rows_and_cleanup_keeps_shared_archive(lookup_context):
    from app.admissions import SourceSnapshot
    from app.database import BrowserSession
    from app.main import utcnow
    from app.maintenance import cleanup_expired_sessions
    client,app=lookup_context;start(client)
    assert client.post('/api/v1/subscriptions',json=confirm(client),headers=HEADERS).status_code==201
    with Session(app.state.engine) as db:
        db.scalar(select(BrowserSession)).expires_at=utcnow()-timedelta(seconds=1);db.commit()
    assert client.get('/api/v1/subscriptions').status_code==401
    assert cleanup_expired_sessions(app.state.engine)==1
    with Session(app.state.engine) as db:
        for model in (Subscription,Assessment,OperationRecord):assert db.scalar(select(func.count()).select_from(model))==0
        assert db.scalar(select(func.count()).select_from(SourceSnapshot))==1


def test_batch_archive_cards_keep_twenty_identities_and_explicit_missing_row(lookup_context,tmp_path):
    client,app=lookup_context;start(client)
    for index in range(1,21):
        assert client.post('/api/v1/subscriptions',json=confirm(client,index),headers=HEADERS).status_code==201
    before=client.get('/api/v1/subscriptions').json()
    assert sorted(x['candidate']['officialRank'] for x in before)==list(range(1,21))
    raw=response();body=b'<!-- synthetic replacement of one fixture code,not observed event -->\n'+raw.body.replace(b'FIXTURE-000001',b'FIXTURE-999999')
    changed=replace(raw,body=body,payload_hash=hashlib.sha256(body).hexdigest(),fetched_at=raw.fetched_at+timedelta(minutes=1))
    registry=app.state.source_registry
    publish(app.state.engine,BINDING.source_id,registry.resolve(BINDING).parse(changed,BINDING),changed,RawStore(tmp_path/'raw'),registry=registry)
    after=client.get('/api/v1/subscriptions').json()
    assert len(after)==20 and len({x['group']['snapshotId'] for x in after})==1
    missing=next(x for x in after if x['id']==before[0]['id'])
    assert missing['candidate'] is None and 'не подтверждает' in missing['notice']
    assert sorted(x['candidate']['officialRank'] for x in after if x['candidate'])==list(range(2,21))
    history=client.get(f"/api/v1/subscriptions/{missing['id']}/history").json()
    assert history['total']==2 and history['items'][0]['present'] is False and history['items'][0]['candidate'] is None
    assert history['items'][1]['candidate']['officialRank']==1
