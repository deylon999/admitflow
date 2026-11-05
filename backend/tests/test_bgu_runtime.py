import json
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import func,select
from sqlalchemy.orm import Session

from app.admissions import CandidateEntry,SourceSnapshot,Subscription
from app.config import Settings
from app.coverage import coverage
from app.jobs import enqueue
from app.main import create_app
from app.sources.audit import audit_source
from app.sources.profile_registration import register_profile
from app.sources.registry import runtime_registry
from app.sources.storage import RawStore
from app.sources.table_profiles import PROFILES
from native_support import postgres_engine
from test_filtered_table import KEY,NOW,response
from test_api import HEADERS,start

pytestmark=pytest.mark.postgres
PROFILE=PROFILES['bgu-2026-080301-contract']


def test_bgu_native_worker_minimal_code_owner_confirmation_and_export(postgres_engine,tmp_path,monkeypatch):
    from app.worker import run_once
    monkeypatch.setenv('SOURCE_IDENTITY_KEY',KEY.hex());registry=runtime_registry();store=RawStore(tmp_path/'raw')
    register_profile(postgres_engine,PROFILE,enable=True,registry=registry);assert enqueue(postgres_engine,PROFILE.source_id,now=NOW)
    assert run_once(postgres_engine,store,registry=registry,fetch=lambda *a,**kw:response(),now=lambda:NOW)['state']=='success'
    assert audit_source(postgres_engine,store,PROFILE.source_id,registry=registry)['success']
    app=create_app(Settings(database_url=postgres_engine.url.render_as_string(hide_password=False),auto_create_schema=False))
    with TestClient(app) as client:
        group=client.get('/api/v1/groups').json()['items'][0]
        assert group['lookupCodeHint']==PROFILE.lookup_code_hint and group['funding']=='contract'
        assert group['seats']==20 and group['rowCount']==109 and not group['scenarioAvailable']
        start(client)
        found=client.post(f'/api/v1/sources/{PROFILE.source_id}/lookup',json=dict(publicCode='70001'),headers=HEADERS)
        assert found.status_code==200 and found.json()['found']
        data=found.json();assert data['candidate']['officialRank']==1 and data['candidate']['participation']=='enrolled'
        assert data['candidate']['consent'] is None and data['candidate']['priority'] is None
        assert '"70001"' not in found.text and '00000000000' not in found.text and 'publicCode' not in found.text
        token=data['confirmationToken'];saved=client.post('/api/v1/subscriptions',json=dict(confirmationToken=token),headers=HEADERS)
        assert saved.status_code==201
        replay=client.post('/api/v1/subscriptions',json=dict(confirmationToken=token),headers=HEADERS)
        assert replay.status_code==201 and replay.json()==saved.json()
        exported=client.get('/api/v1/archive-export');assert exported.status_code==200
        assert '"70001"' not in exported.text and '00000000000' not in exported.text and 'candidateKey' not in exported.text
        bad=client.post(f'/api/v1/sources/{PROFILE.source_id}/lookup',json=dict(publicCode='70001/00000000000/0000001'),headers=HEADERS)
        assert bad.status_code==422 and '00000000000' not in bad.text
        with TestClient(app) as other:
            start(other)
            assert other.get('/api/v1/subscriptions').json()==[]
            assert other.post('/api/v1/subscriptions',json=dict(confirmationToken=token),headers=HEADERS).status_code==403
    with Session(postgres_engine) as db:
        assert db.scalar(select(func.count()).select_from(CandidateEntry))==109
        assert db.scalar(select(func.count()).select_from(SourceSnapshot))==1
        assert db.scalar(select(func.count()).select_from(Subscription))==1
        counts=coverage(db,registry=registry,now=NOW)
        assert counts['importedGroups']==counts['archiveImportedGroups']==counts['importedUniversities']==1
        assert counts['importedRows']==109 and counts['freshGroups']==counts['conditionalGroups']==0
