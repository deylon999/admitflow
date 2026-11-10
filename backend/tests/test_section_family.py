from app.accreditation_registry import load_registry
from dataclasses import replace
from datetime import datetime,timezone
import hashlib
from pathlib import Path
from urllib.parse import urlsplit

from bs4 import BeautifulSoup
import pytest

from app.sources.contracts import AdapterError,SourceBinding
from app.sources.fetcher import FetchResult
from app.sources.table_family import SECTION_VERSION,parse_table,make_table_adapter
from app.sources.table_profiles import PROFILES
from native_support import postgres_engine

ROOT=Path(__file__).resolve().parents[2]
SCOPES=tuple(p for p in PROFILES.values() if p.version==SECTION_VERSION)
NOW=datetime(2026,11,5,tzinfo=timezone.utc)
KEY=b'synthetic-section-family-key-00001'


def binding(p):
    return SourceBinding(p.source_id,p.group_id,p.year,p.url,urlsplit(p.url).hostname,p.version,p.kind,True)


def response(p,body=None):
    body=(ROOT/p.proof.fixture).read_bytes() if body is None else body
    return FetchResult(p.url,body,'text/html',hashlib.sha256(body).hexdigest(),NOW,'utf-8')


@pytest.mark.parametrize('profile',SCOPES,ids=lambda p:p.source_id)
def test_reviewed_section_keeps_scope_contract_unknowns_and_exact_evidence(profile):
    raw=response(profile);parsed=parse_table(raw,binding(profile),KEY,profile)
    assert raw.payload_hash==profile.proof.fixture_sha256
    assert (ROOT/profile.proof.passport).is_file()
    assert b'SYNTHETIC CANDIDATE VALUES' in raw.body
    assert len(parsed.entries)==profile.rows and parsed.seats==profile.seats and parsed.kind=='archive'
    assert parsed.source_updated_at is None
    assert all(row.consent is None and row.participation=='unknown' for row in parsed.entries)
    assert all(row.priority is None for row in parsed.entries[4::5])
    assert [row.official_rank for row in parsed.entries]==list(range(1,profile.rows+1))


def test_two_sections_on_one_url_are_separate_groups_and_identities():
    scopes=tuple(p for p in SCOPES if p.section_count==2)
    assert len(scopes)==2 and scopes[0].url==scopes[1].url
    adapter=make_table_adapter(KEY,SCOPES,version=SECTION_VERSION)
    assert len(adapter.proofs)==10
    parsed=[adapter.parse(response(p),binding(p)) for p in scopes]
    assert {len(p.entries) for p in parsed}=={2,13}
    assert parsed[0].entries[0].candidate_key!=parsed[1].entries[0].candidate_key
    with pytest.raises(AdapterError):adapter.parse(response(scopes[0]),replace(binding(scopes[0]),source_id='unreviewed'))
    with pytest.raises(ValueError,match='incomplete_page_attestation'):
        make_table_adapter(KEY,[scopes[0]],version=SECTION_VERSION)


@pytest.mark.parametrize('damage',['metadata','sections','swapped','span','year','group','header','duplicate','truncated','pagination'])
def test_changed_or_ambiguous_section_fails_closed(damage):
    p=next(p for p in SCOPES if p.section_count==2 and p.section_index==0)
    raw=response(p);doc=BeautifulSoup(raw.body,'html.parser')
    section=doc.select(p.section_selector)[0];table=section.select_one(p.table_selector)
    if damage=='metadata':section.find_previous_sibling('tr').td.string='Different competition'
    elif damage=='sections':doc.select(p.section_selector)[-1].decompose()
    elif damage=='swapped':
        last=doc.select(p.section_selector)[-1];section.replace_with(last.extract())
    elif damage=='span':table.select('th')[2]['colspan']='4'
    elif damage=='year':doc.select_one(p.season_selector).string='2027 г.'
    elif damage=='group':doc.select_one(p.identity[0][0]).string='Other group'
    elif damage=='header':table.select('th')[1].string='Other ID'
    elif damage=='duplicate':
        rows=[r for r in table.select('tr') if r.find_all('td',recursive=False)]
        rows[1].find_all('td')[1].string='FIXTURE-000001'
    elif damage=='pagination':doc.body.append(BeautifulSoup('<a rel="next">2</a>','html.parser').a)
    body=str(doc).encode() if damage!='truncated' else raw.body[:len(raw.body)//2]
    with pytest.raises(AdapterError):parse_table(response(p,body),binding(p),KEY,p)
    for change in ({'year':2027},{'kind':'live'},{'group_id':'other-group'}):
        with pytest.raises(AdapterError):parse_table(raw,replace(binding(p),**change),KEY,p)


@pytest.mark.postgres
def test_all_scopes_publish_to_native_pg_without_inflating_catalog_or_coverage(postgres_engine,tmp_path,monkeypatch):
    from sqlalchemy import select,func
    from sqlalchemy.orm import Session
    from app.admissions import CandidateEntry,SourceSnapshot
    from app.catalog import catalog_size
    from app.coverage import coverage
    from app.jobs import enqueue
    from app.sources.audit import audit_source
    from app.sources.profile_registration import register_profile
    from app.sources.registry import runtime_registry
    from app.sources.status import source_status
    from app.sources.storage import RawStore
    from app.worker import run_once
    monkeypatch.setenv('SOURCE_IDENTITY_KEY',KEY.hex());registry=runtime_registry();store=RawStore(tmp_path/'raw')
    for p in SCOPES:
        assert register_profile(postgres_engine,p,registry=registry)['enabled'] is False
        assert register_profile(postgres_engine,p,enable=True,registry=registry)['enabled'] is True
        assert enqueue(postgres_engine,p.source_id,now=NOW)
    for _ in SCOPES:
        assert run_once(postgres_engine,store,registry=registry,fetch=lambda b,*a,**kw:response(PROFILES[b.source_id]),now=lambda:NOW)['state']=='success'
    assert run_once(postgres_engine,store,registry=registry,now=lambda:NOW)['state']=='idle'
    for p in SCOPES:assert audit_source(postgres_engine,store,p.source_id,registry=registry)['success']
    with Session(postgres_engine) as db:
        assert db.scalar(select(func.count()).select_from(CandidateEntry))==168
        assert db.scalar(select(func.count()).select_from(SourceSnapshot))==11
        assert catalog_size(db)==1257
        data=coverage(db,registry=registry,now=NOW)
        assert data['importedUniversities']==2 and data['importedGroups']==data['archiveImportedGroups']==11
        assert data['importedRows']==168 and data['automaticSources']==data['freshGroups']==data['conditionalGroups']==0
        assert data['nationalTotal']==load_registry().denominator
        assert all(source_status(db,p.source_id,registry=registry,now=NOW)['state']=='archived' for p in SCOPES)
