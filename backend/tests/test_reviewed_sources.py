from dataclasses import replace
from datetime import datetime,timezone
import hashlib
from pathlib import Path
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import func,select
from sqlalchemy.orm import Session
from app.admissions import CandidateEntry,SourceSnapshot,Source,University
from app.config import Settings
from app.main import create_app
from app.jobs import enqueue
from app.sources.profile_registration import register_profile
from app.sources.table_profiles import SGU,GUAP,PROFILES
from app.sources.registry import Registry
from app.sources.storage import RawStore
from app.sources.fetcher import FetchResult
from app.worker import run_once
from test_api import HEADERS,start
from test_sgu_adapter import KEY
from test_table_family import fetch,binding
from native_support import postgres_engine

pytestmark=pytest.mark.postgres


@pytest.fixture
def reviewed_context(postgres_engine,monkeypatch,tmp_path):
    monkeypatch.setenv('SOURCE_IDENTITY_KEY',KEY.hex())
    app=create_app(Settings(database_url=postgres_engine.url.render_as_string(hide_password=False),auto_create_schema=False))
    with TestClient(app) as client:yield client,app,RawStore(tmp_path/'raw')


def test_reviewed_family_real_format_worker_and_owner_api_for_both_universities(reviewed_context):
    client,app,store=reviewed_context
    for profile in (SGU,GUAP):
        disabled=register_profile(app.state.engine,profile,registry=app.state.source_registry)
        assert disabled['enabled'] is False
        enabled=register_profile(app.state.engine,profile,enable=True,registry=app.state.source_registry)
        assert enabled['enabled'] and enabled['created'] is False
        assert enqueue(app.state.engine,profile.source_id,now=fetch(profile).fetched_at)
    sources={p.source_id:p for p in (SGU,GUAP)}
    outcomes=[run_once(app.state.engine,store,registry=app.state.source_registry,fetch=lambda b,*_,**__:fetch(sources[b.source_id]),now=lambda:fetch(SGU).fetched_at) for _ in range(2)]
    assert {r['sourceId'] for r in outcomes}==set(sources) and all(r['state']=='success' for r in outcomes)
    assert run_once(app.state.engine,store,registry=app.state.source_registry,now=lambda:fetch(SGU).fetched_at)['state']=='idle'
    catalog=client.get('/api/v1/groups').json()['items']
    assert {g['rowCount'] for g in catalog}=={573,581} and all(g['coverage']=='archive' and g['lookupAvailable'] for g in catalog)
    start(client);tokens=[]
    for profile in (SGU,GUAP):
        found=client.post(f'/api/v1/sources/{profile.source_id}/lookup',json={'publicCode':'FIXTURE-000001'},headers=HEADERS)
        assert found.status_code==200 and found.json()['found'];tokens.append(found.json()['confirmationToken'])
        assert client.post('/api/v1/subscriptions',json={'confirmationToken':tokens[-1]},headers=HEADERS).status_code==201
    assert len(set(tokens))==2
    records=client.get('/api/v1/subscriptions').json();assert len(records)==2
    paid=next(r for r in records if r['group']['sourceId']==GUAP.source_id)
    assert paid['group']['funding']=='contract' and paid['group']['seats']==0 and paid['candidate']['consent'] is None
    assert all(x['group']['assessmentAvailable'] is False for x in records)
    with TestClient(app) as other:
        start(other);assert other.get('/api/v1/subscriptions').json()==[]
        assert other.post('/api/v1/subscriptions',json={'confirmationToken':tokens[0]},headers=HEADERS).status_code==403
    with Session(app.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(CandidateEntry))==1154
        assert db.scalar(select(func.count()).select_from(SourceSnapshot))==2
    for profile in (SGU,GUAP):
        proof=profile.proof;root=Path(__file__).resolve().parents[2]
        assert (root/proof.passport).is_file() and hashlib.sha256((root/proof.fixture).read_bytes()).hexdigest()==proof.fixture_sha256


def test_failed_key_or_conflicting_registration_rolls_back(reviewed_context):
    client,app,_=reviewed_context
    from app.sources.contracts import AdapterError
    with pytest.raises(AdapterError):register_profile(app.state.engine,GUAP,enable=True,registry=Registry())
    with Session(app.state.engine) as db:assert db.get(Source,GUAP.source_id) is None and db.get(University,'guap-spb') is None
    register_profile(app.state.engine,GUAP,registry=app.state.source_registry)
    broken=replace(GUAP,seats=1)
    with pytest.raises(AdapterError,match='invalid_binding'):register_profile(app.state.engine,broken,enable=True,registry=app.state.source_registry)
    with Session(app.state.engine) as db:assert db.get(Source,GUAP.source_id).enabled is False


def test_generic_profile_cannot_silently_replace_published_legacy_version(reviewed_context):
    from app.sources.pilots import register_sgu
    from app.sources.contracts import AdapterError
    from app.sources.adapters.sgu2026 import VERSION as LEGACY
    _,app,_=reviewed_context
    register_sgu(app.state.engine,enable=True,registry=app.state.source_registry)
    with pytest.raises(AdapterError,match='invalid_binding'):register_profile(app.state.engine,SGU,enable=True,registry=app.state.source_registry)
    with Session(app.state.engine) as db:assert db.get(Source,SGU.source_id).adapter_version==LEGACY
