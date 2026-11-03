from datetime import datetime,timezone

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import func,select
from sqlalchemy.orm import Session

from app.admissions import Subscription
from app.config import Settings
from app.database import OperationRecord,Watch
from app.main import create_app
from app.source_tokens import Confirmation,ConfirmationError,issue,verify
from app.sources.pilots import register_sgu
from app.sources.publishing import publish
from app.sources.storage import RawStore
from test_api import HEADERS,start
from test_sgu_adapter import BINDING,KEY,response


@pytest.fixture
def lookup_context(tmp_path,monkeypatch):
    monkeypatch.setenv('SOURCE_IDENTITY_KEY',KEY.hex())
    app=create_app(Settings(database_url=f'sqlite:///{tmp_path}/lookup.db'))
    with TestClient(app) as client:
        register_sgu(app.state.engine,enable=True,registry=app.state.source_registry)
        raw=response();parsed=app.state.source_registry.resolve(BINDING).parse(raw,BINDING)
        publish(app.state.engine,BINDING.source_id,parsed,raw,RawStore(tmp_path/'raw'),registry=app.state.source_registry)
        yield client,app


def test_lookup_requires_guest_and_never_creates_a_subscription(lookup_context):
    client,app=lookup_context;path=f'/api/v1/sources/{BINDING.source_id}/lookup'
    body={'publicCode':'FIXTURE-000001'}
    assert client.post(path,json=body,headers=HEADERS).status_code==401
    start(client)
    result=client.post(path,json=body,headers=HEADERS)
    assert result.status_code==200
    value=result.json()
    assert value['found'] and value['candidate']['officialRank']==1 and value['group']['year']==2026
    assert value['group']['dataKind']=='archive' and value['group']['assessmentAvailable'] is False
    assert value['confirmationToken'] and value['expiresAt']
    assert 'FIXTURE-' not in result.text and 'candidateKey' not in result.text
    with Session(app.state.engine) as db:
        for model in (Subscription,Watch,OperationRecord):assert db.scalar(select(func.count()).select_from(model))==0
    missing=client.post(path,json={'publicCode':'not-present'},headers=HEADERS).json()
    assert missing['found'] is False and missing['candidate'] is None and missing['confirmationToken'] is None


def test_invalid_lookup_does_not_echo_code_or_accept_other_sources(lookup_context):
    client,_=lookup_context;start(client);path=f'/api/v1/sources/{BINDING.source_id}/lookup'
    invalid='private-code<script>'
    response=client.post(path,json={'publicCode':invalid},headers=HEADERS)
    assert response.status_code==422 and invalid not in response.text
    assert client.post('/api/v1/sources/other-source/lookup',json={'publicCode':'FIXTURE-000001'},headers=HEADERS).status_code==404
    assert client.post(path,json={'publicCode':'FIXTURE-000001'}).status_code==403


def test_confirmation_is_owner_scoped_tamper_evident_and_expires():
    claims=Confirmation(version=1,source_id='s',group_id='g',snapshot_id='snapshot',candidate_key='a'*64,expires=110)
    token=issue(claims,'owner-a',KEY)
    assert verify(token,'owner-a',KEY,100)==claims
    assert 'owner-a' not in token
    for owner,changed,key in [('owner-b',token,KEY),('owner-a',token[:-1]+('0' if token[-1]!='0' else '1'),KEY),('owner-a',token,b'z'*32)]:
        with pytest.raises(ConfirmationError,match='invalid'):verify(changed,owner,key,100)
    with pytest.raises(ConfirmationError,match='expired'):verify(token,'owner-a',KEY,110)
    with pytest.raises(ConfirmationError,match='invalid'):verify('x'*2049,'owner-a',KEY,100)


def test_lookup_budget_is_shared_by_requests_resets_and_does_not_store_codes(lookup_context,monkeypatch):
    from datetime import timedelta
    from app.main import utcnow
    from app.database import LookupBudget
    client,app=lookup_context;start(client)
    path=f'/api/v1/sources/{BINDING.source_id}/lookup'
    now=utcnow();monkeypatch.setattr('app.main.utcnow',lambda:now)
    for _ in range(30):assert client.post(path,json={'publicCode':'not-present'},headers=HEADERS).status_code==200
    limited=client.post(path,json={'publicCode':'FIXTURE-000001'},headers=HEADERS)
    assert limited.status_code==429 and limited.headers['retry-after']=='60'
    with Session(app.state.engine) as db:
        assert db.scalar(select(LookupBudget)).used==30
        assert set(LookupBudget.__table__.columns.keys())=={'owner_hash','window_start','used'}
    monkeypatch.setattr('app.main.utcnow',lambda:now+timedelta(seconds=60))
    assert client.post(path,json={'publicCode':'FIXTURE-000001'},headers=HEADERS).status_code==200
    assert client.delete('/api/v1/session',headers=HEADERS).status_code==204
    with Session(app.state.engine) as db:assert db.scalar(select(func.count()).select_from(LookupBudget))==0
