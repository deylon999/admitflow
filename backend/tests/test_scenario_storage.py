from dataclasses import replace
from datetime import timedelta
import hashlib
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import select,func
from sqlalchemy.orm import Session
from app.admissions import Assessment,SourceSnapshot,PublishedSnapshot,Subscription,CandidateEntry
from app.scenario_storage import enable_scenarios
from app.scenarios import VERSION,assess
from app.sources.publishing import publish
from app.sources.storage import RawStore
from test_api import HEADERS,start
from test_source_lookup import lookup_context
from test_sgu_adapter import BINDING,response
from test_subscriptions import confirm


def changed_consent(app,tmp_path):
    raw=response();soup=BeautifulSoup(raw.body,'html.parser');cell=soup.select_one('td[data-label="Согласие на зачисление"]');cell.clear();cell.append('Да')
    body=('<!-- synthetic consent change for deterministic replay;not observed event -->\n'+str(soup)).encode()
    fetched=replace(raw,body=body,payload_hash=hashlib.sha256(body).hexdigest(),fetched_at=raw.fetched_at+timedelta(minutes=1))
    registry=app.state.source_registry
    parsed=registry.resolve(BINDING).parse(fetched,BINDING)
    return parsed,fetched


def test_versioned_scenario_reproduces_diff_and_history_without_mutation(lookup_context,tmp_path,monkeypatch):
    client,app=lookup_context;start(client)
    enable_scenarios(app.state.engine,BINDING.source_id,registry=app.state.source_registry)
    body=confirm(client,20);saved=client.post('/api/v1/subscriptions',json=body,headers=HEADERS).json();path=f"/api/v1/subscriptions/{saved['id']}/scenario"
    initial=client.get(path).json();assert initial['available'] and initial['result']['modelVersion']==VERSION and initial['result']['numbers']
    with Session(app.state.engine) as db:
        sub=db.get(Subscription,saved['id']);snapshot=db.get(SourceSnapshot,initial['snapshotId']);rows=db.scalars(select(CandidateEntry).where(CandidateEntry.snapshot_id==snapshot.id).order_by(CandidateEntry.official_rank)).all()
        reproduced=assess(rows,sub.candidate_key,funding='budget',category='general',seats=snapshot.seats)
        assert reproduced.model_dump(mode='json',by_alias=True)==initial['result']
    parsed,raw=changed_consent(app,tmp_path)
    for _ in range(2):publish(app.state.engine,BINDING.source_id,parsed,raw,RawStore(tmp_path/'raw'),registry=app.state.source_registry)
    current=client.get(path).json();assert current['result']['numbers']['currentLower']==initial['result']['numbers']['currentLower']+1
    assert {'currentLower','currentUpper','consentYesAbove','consentNoAbove'}<={x['field'] for x in current['changes']}
    assert current['result']['numbers']['allConsentPlace']==initial['result']['numbers']['allConsentPlace']
    history=client.get(path+'-history',params={'limit':1}).json();assert history['total']==2 and history['nextCursor']
    older=client.get(path+'-history',params={'before':history['nextCursor']}).json();assert older['items']==[initial]
    monkeypatch.setattr('app.scenario_storage.assess',lambda *_,**__:(_ for _ in ()).throw(AssertionError('GET must not recalculate')))
    assert client.get(path).json()==current
    with Session(app.state.engine) as db:assert db.scalar(select(func.count()).select_from(Assessment).where(Assessment.rules_version==VERSION))==2
    with TestClient(app) as other:
        start(other);assert other.get(path).status_code==404 and other.get(path+'-history').status_code==404
    assert client.get(path+'-history',params={'before':'foreign'}).status_code==400
    assert client.post('/api/v1/subscriptions',json=body,headers=HEADERS).status_code==201


def test_assessment_failure_rolls_back_all_publication_and_preserves_previous(lookup_context,tmp_path,monkeypatch):
    client,app=lookup_context;start(client);enable_scenarios(app.state.engine,BINDING.source_id,registry=app.state.source_registry)
    saved=client.post('/api/v1/subscriptions',json=confirm(client,20),headers=HEADERS).json();path=f"/api/v1/subscriptions/{saved['id']}/scenario";before=client.get(path).json()
    parsed,raw=changed_consent(app,tmp_path)
    def fail(*_,**__):raise RuntimeError('Injected scenario transaction failure')
    monkeypatch.setattr('app.scenario_storage.append_source',fail)
    with pytest.raises(RuntimeError,match='Injected'):publish(app.state.engine,BINDING.source_id,parsed,raw,RawStore(tmp_path/'raw'),registry=app.state.source_registry)
    assert client.get(path).json()==before
    with Session(app.state.engine) as db:assert db.get(PublishedSnapshot,BINDING.source_id).snapshot_id==before['snapshotId'] and db.scalar(select(func.count()).select_from(SourceSnapshot))==1


def test_explicit_policy_backfills_existing_subscription_and_declines_paid_source(lookup_context,tmp_path):
    from app.sources.profile_registration import register_profile
    from app.sources.table_profiles import GUAP
    from test_table_family import fetch,binding
    client,app=lookup_context;start(client)
    saved=client.post('/api/v1/subscriptions',json=confirm(client,20),headers=HEADERS).json();path=f"/api/v1/subscriptions/{saved['id']}/scenario"
    assert client.get(path).json()['available'] is False
    for _ in range(2):enable_scenarios(app.state.engine,BINDING.source_id,registry=app.state.source_registry)
    assert client.get(path).json()['available']
    register_profile(app.state.engine,GUAP,enable=True,registry=app.state.source_registry);raw=fetch(GUAP)
    publish(app.state.engine,GUAP.source_id,app.state.source_registry.resolve(binding(GUAP)).parse(raw,binding(GUAP)),raw,RawStore(tmp_path/'raw'),registry=app.state.source_registry)
    enable_scenarios(app.state.engine,GUAP.source_id,registry=app.state.source_registry)
    found=client.post(f'/api/v1/sources/{GUAP.source_id}/lookup',json={'publicCode':'FIXTURE-000001'},headers=HEADERS).json()
    paid=client.post('/api/v1/subscriptions',json={'confirmationToken':found['confirmationToken']},headers=HEADERS).json()
    value=client.get(f"/api/v1/subscriptions/{paid['id']}/scenario").json()
    assert value['available'] and value['result']['state']=='unsupported' and value['result']['numbers'] is None
    assert value['result']['reasonCodes']==['unsupported_funding']
    groups=client.get('/api/v1/groups').json()['items'];assert next(g for g in groups if g['id']==BINDING.group_id)['scenarioAvailable'] is True
    assert next(g for g in groups if g['id']==GUAP.group_id)['scenarioAvailable'] is False
