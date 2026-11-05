from dataclasses import replace
from datetime import datetime,timezone
import hashlib
from pathlib import Path
import pytest

from app.sources.contracts import AdapterError,SourceBinding
from app.sources.fetcher import FetchResult
from app.sources.table_family import VERSION,parse_table
from app.sources.table_profiles import PROFILES
from native_support import postgres_engine

PROFILE=PROFILES['sgu-2026-4576']
BODY=(Path(__file__).resolve().parents[2]/PROFILE.proof.fixture).read_bytes()
NOW=datetime(2026,11,5,tzinfo=timezone.utc)
KEY=b'new-scope-synthetic-test-key-00001'


def binding():
    return SourceBinding(PROFILE.source_id,PROFILE.group_id,2026,PROFILE.url,'www.sgu.ru',PROFILE.version,'archive',True)


def response(body=BODY):
    return FetchResult(PROFILE.url,body,'text/html',hashlib.sha256(body).hexdigest(),NOW,'utf-8')


def test_next_scope_uses_same_parser_with_synthetic_fixture_and_exact_proof():
    parsed=parse_table(response(),binding(),KEY,PROFILE)
    assert len(parsed.entries)==453 and parsed.seats==24 and parsed.kind=='archive'
    assert hashlib.sha256(BODY).hexdigest()==PROFILE.proof.fixture_sha256
    assert 'SYNTHETIC CANDIDATE ROWS' in BODY.decode()
    assert [row.official_rank for row in parsed.entries]==list(range(1,454))
    assert sum(row.consent is True for row in parsed.entries)==151
    for scope in (replace(binding(),year=2027),replace(binding(),kind='live'),replace(binding(),group_id='other')):
        with pytest.raises(AdapterError):parse_table(response(),scope,KEY,PROFILE)
    with pytest.raises(AdapterError):parse_table(response(BODY[:len(BODY)//2]),binding(),KEY,PROFILE)
    with pytest.raises(AdapterError):parse_table(response(),binding(),KEY,replace(PROFILE,rows=452))


def test_v2_accepts_only_reviewed_exam_alternative_order_and_v1_remains_strict():
    from bs4 import BeautifulSoup
    from app.sources.table_profiles import SGU
    doc=BeautifulSoup(BODY,'html.parser')
    alternatives=' / '.join(reversed(PROFILE.unordered_label_groups[0]))
    doc.select('th')[8].string='Экз. 1 '+alternatives
    for row in doc.select(PROFILE.row_selector):row.find_all('td',recursive=False)[3]['data-label']=alternatives
    reordered=str(doc).encode()
    assert parse_table(response(reordered),binding(),KEY,PROFILE).entries==parse_table(response(),binding(),KEY,PROFILE).entries
    doc.select('th')[8].string='Экз. 1 '+alternatives+' / Неизвестный экзамен'
    with pytest.raises(AdapterError):parse_table(response(str(doc).encode()),binding(),KEY,PROFILE)
    with pytest.raises(ValueError):replace(SGU,unordered_label_groups=PROFILE.unordered_label_groups)
    with pytest.raises(AdapterError):parse_table(replace(response(),payload_hash='0'*64),binding(),KEY,PROFILE)


@pytest.mark.postgres
def test_next_scope_real_pg_worker_is_explicit_idempotent_and_shown_as_archive(postgres_engine,tmp_path,monkeypatch):
    from sqlalchemy import select,func
    from sqlalchemy.orm import Session
    from app.admissions import CandidateEntry,Source,SourceSnapshot
    from app.jobs import enqueue
    from app.sources.profile_registration import register_profile
    from app.sources.registry import runtime_registry
    from app.sources.storage import RawStore
    from app.worker import run_once
    monkeypatch.setenv('SOURCE_IDENTITY_KEY',KEY.hex());registry=runtime_registry()
    assert register_profile(postgres_engine,PROFILE,registry=registry)['enabled'] is False
    assert register_profile(postgres_engine,PROFILE,enable=True,registry=registry)['enabled'] is True
    assert enqueue(postgres_engine,PROFILE.source_id,now=NOW)
    store=RawStore(tmp_path/'raw')
    assert run_once(postgres_engine,store,registry=registry,fetch=lambda *_args,**_kwargs:response(),now=lambda:NOW)['state']=='success'
    assert run_once(postgres_engine,store,registry=registry,fetch=lambda *_args,**_kwargs:response(),now=lambda:NOW)['state']=='idle'
    from app.sources.status import source_status
    with Session(postgres_engine) as db:
        assert db.scalar(select(func.count()).select_from(CandidateEntry))==453
        assert db.scalar(select(func.count()).select_from(SourceSnapshot))==1
        assert db.get(Source,PROFILE.source_id).group_id==PROFILE.group_id
        status=source_status(db,PROFILE.source_id,registry=registry,now=NOW)
        assert status['state']=='archived' and status['dataKind']=='archive'
