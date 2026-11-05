from concurrent.futures import ThreadPoolExecutor
import json

import pytest
from sqlalchemy import func,select
from sqlalchemy.orm import Session

from app.admissions import CompetitionGroup,Source,SourceOperation,University
from app.sources.batch import main
from app.sources.contracts import AdapterError
from app.sources.profile_registration import register_profile,register_profiles,select_profiles
from app.sources.registry import Registry,runtime_registry
from app.sources.table_profiles import PROFILES
from native_support import postgres_engine

KEY=b'synthetic-batch-registration-key-01'
IDS=tuple(sorted(PROFILES))


def verify_batch(engine,monkeypatch):
    monkeypatch.setenv('SOURCE_IDENTITY_KEY',KEY.hex());registry=runtime_registry()
    with pytest.raises(AdapterError):register_profiles(engine,IDS,enable=True,registry=Registry())
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(Source))==0
        assert db.scalar(select(func.count()).select_from(University))==0
    result=register_profiles(engine,IDS,registry=registry)
    assert result['atomic'] and result['count']==result['created']==len(IDS)
    assert not any(row['enabled'] for row in result['items'])
    replay=register_profiles(engine,tuple(reversed(IDS)),enable=True,registry=registry)
    assert replay['created']==0 and all(row['enabled'] for row in replay['items'])
    assert [row['sourceId'] for row in replay['items']]==list(reversed(IDS))
    last=PROFILES[IDS[-1]]
    with Session(engine) as db:
        db.get(CompetitionGroup,last.group_id).seats+=1;db.commit()
        journal_before=db.scalar(select(func.count()).select_from(SourceOperation))
    with pytest.raises(AdapterError,match='invalid_binding'):register_profiles(engine,IDS,enable=True,registry=registry)
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(SourceOperation))==journal_before
        assert db.scalar(select(func.count()).select_from(Source))==len(IDS)
    return registry


def test_profile_batch_is_atomic_idempotent_and_closed_on_sqlite(source_engine,monkeypatch):verify_batch(source_engine,monkeypatch)


@pytest.mark.postgres
def test_profile_batch_is_atomic_idempotent_and_closed_on_postgres(postgres_engine,monkeypatch):verify_batch(postgres_engine,monkeypatch)


@pytest.mark.parametrize('ids',[[],['unknown'],['https://example.org/list'],[IDS[0],IDS[0]],[None],['unknown']*101,'all'])
def test_invalid_selections_cannot_open_a_database(ids,monkeypatch,capsys):
    monkeypatch.setattr('app.sources.batch.make_engine',lambda *_:pytest.fail('must reject before database access'))
    with pytest.raises(AdapterError):select_profiles(ids)
    if isinstance(ids,list) and ids and all(isinstance(x,str) for x in ids):assert main(ids)==1
    assert KEY.hex() not in capsys.readouterr().out


def test_plan_lists_closed_scope_metadata_without_database_or_key(monkeypatch,capsys):
    monkeypatch.delenv('SOURCE_IDENTITY_KEY',raising=False)
    monkeypatch.setattr('app.sources.batch.make_engine',lambda *_:pytest.fail('plan must not connect'))
    assert main(['--plan','--enable',*IDS])==0
    data=json.loads(capsys.readouterr().out)
    assert data['readOnly'] and data['count']==len(IDS) and data['databaseChecked'] is False
    assert all(set(item)=={'sourceId','groupId','year','kind','adapterVersion'} for item in data['items'])


def test_quarantine_at_end_rolls_back_earlier_new_scopes(source_engine,monkeypatch):
    from app.source_operations import control
    monkeypatch.setenv('SOURCE_IDENTITY_KEY',KEY.hex());registry=runtime_registry()
    register_profile(source_engine,PROFILES[IDS[-1]],registry=registry)
    control(source_engine,IDS[-1],'quarantine',registry=registry)
    with pytest.raises(AdapterError,match='operator_quarantine'):register_profiles(source_engine,IDS,enable=True,registry=registry)
    with Session(source_engine) as db:
        assert db.scalar(select(func.count()).select_from(Source))==1
        assert db.get(Source,IDS[-1]).last_error_code=='operator_quarantine'
        assert db.scalar(select(func.count()).select_from(SourceOperation))==2


@pytest.mark.postgres
def test_overlapping_batches_and_single_registration_share_catalog_mutex(postgres_engine,monkeypatch):
    monkeypatch.setenv('SOURCE_IDENTITY_KEY',KEY.hex());registry=runtime_registry()
    scopes=[p for p in PROFILES.values() if p.source_id.startswith('section-110420-')][:4]
    def run(index):
        if index==0:return register_profile(postgres_engine,scopes[0],enable=True,registry=registry)
        return register_profiles(postgres_engine,[p.source_id for p in scopes[index%3:index%3+2]],enable=True,registry=registry)
    with ThreadPoolExecutor(max_workers=8) as pool:results=list(pool.map(run,range(8)))
    created=sum(value['created'] for value in results)
    assert created==4
    with Session(postgres_engine) as db:
        assert db.scalar(select(func.count()).select_from(University))==1
        assert db.scalar(select(func.count()).select_from(Source))==4
        assert all(db.get(Source,p.source_id).enabled for p in scopes)


@pytest.mark.postgres
def test_batch_cannot_replace_an_existing_legacy_parser(postgres_engine,monkeypatch):
    from app.sources.pilots import register_sgu
    from app.sources.adapters.sgu2026 import VERSION
    monkeypatch.setenv('SOURCE_IDENTITY_KEY',KEY.hex());registry=runtime_registry()
    register_sgu(postgres_engine,enable=True,registry=registry)
    with pytest.raises(AdapterError,match='invalid_binding'):register_profiles(postgres_engine,IDS,enable=True,registry=registry)
    with Session(postgres_engine) as db:
        assert db.scalar(select(func.count()).select_from(Source))==1
        assert db.get(Source,'sgu-2026-4588').adapter_version==VERSION


@pytest.mark.postgres
def test_maximum_batch_of_one_hundred_synthetic_profiles_stays_disabled(postgres_engine,monkeypatch):
    from dataclasses import replace
    from types import MappingProxyType
    from app.sources import table_profiles
    from app.admissions import SourceSnapshot
    from app.jobs import SourceJob
    prototype=PROFILES['guap-2026-math-contract'];profiles={}
    for i in range(100):
        ident=f'synthetic-batch-{i:03d}';url=f'https://fixtures.invalid/{i}'
        metadata={**dict(prototype.catalog),'university_id':'synthetic-batch-u','university_name':'Synthetic batch only',
            'university_url':'https://fixtures.invalid/','campaign_id':'synthetic-batch-c','official_id':str(i)}
        profiles[ident]=replace(prototype,source_id=ident,group_id=ident,url=url,catalog=tuple(metadata.items()),
            proof=replace(prototype.proof,source_url=url,passport='backend/tests/fixtures/synthetic-passport.md'))
    monkeypatch.setattr(table_profiles,'PROFILES',MappingProxyType(profiles))
    result=register_profiles(postgres_engine,list(profiles))
    assert result['count']==result['created']==100 and all(not row['enabled'] for row in result['items'])
    with pytest.raises(AdapterError,match='invalid_binding'):select_profiles([*profiles,'synthetic-over-limit'])
    with Session(postgres_engine) as db:
        assert db.scalar(select(func.count()).select_from(Source))==100
        assert db.scalar(select(func.count()).select_from(SourceSnapshot))==0
        assert db.scalar(select(func.count()).select_from(SourceJob))==0
