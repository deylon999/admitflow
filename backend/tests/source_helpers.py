"""Synthetic source only; never registered in the production registry."""
import hashlib
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.admissions import Campaign, CompetitionGroup, Source, University
from app.sources.contracts import CandidateRow, ParsedList, SourceBinding
from app.sources.fetcher import FetchResult
from app.sources.registry import Adapter, Attestation, Registry

NOW = datetime(2026,11,1,tzinfo=timezone.utc)
BINDING = SourceBinding('source-1','group-1',2026,'https://example.org/list','example.org','synthetic-v1','archive',True)


def seed_source(engine, **source_changes):
    with Session(engine) as db:
        db.add(University(id='synthetic',name='Synthetic only',official_url='https://example.org',provenance_url='https://example.org/list',verified_at=NOW))
        db.flush()
        db.add(Campaign(id='campaign-1',university_id='synthetic',year=2026,level='bachelor'))
        db.flush()
        db.add(CompetitionGroup(id='group-1',campaign_id='campaign-1',official_id='test',title='Synthetic group',study_form='full-time',funding='budget',category='general',seats=10,coverage='candidate'))
        db.flush()
        db.add(Source(**(dict(id='source-1',group_id='group-1',url=BINDING.url,domain=BINDING.domain,adapter_version=BINDING.adapter_version,snapshot_kind='archive',enabled=True)|source_changes)))
        db.commit()


def parsed(count=3, version='synthetic-v1'):
    return ParsedList(source_id='source-1',group_id='group-1',year=2026,adapter_version=version,kind='archive',complete=True,expected_rows=count,seats=10,entries=tuple(CandidateRow(candidate_key=f'{i:064x}',row_ref=f'row/{i}',official_rank=i) for i in range(1,count+1)))


def raw(body=b'synthetic sample', at=NOW):
    return FetchResult(BINDING.url,body,'text/plain',hashlib.sha256(body).hexdigest(),at,'utf-8')


def registry(*versions):
    return Registry(tuple(Adapter(version,frozenset({'example.org'}),lambda response,binding: parsed(version=binding.adapter_version)) for version in (versions or ('synthetic-v1',))))


def synthetic_attestation():
    return Attestation(passport='backend/tests/fixtures/synthetic-passport.md',fixture='backend/tests/fixtures/synthetic-source.txt',
                       fixture_sha256=raw().payload_hash,original_sha256=raw().payload_hash,source_url=BINDING.url,
                       year=2026,kind='archive',sample_rows=3,checked_rows=3,verified_at=NOW,adapter_version='synthetic-v1')
