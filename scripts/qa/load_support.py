"""Synthetic attested adapter for the load stand: example.org only, no network, no real people."""
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import os

from app.sources.contracts import CandidateRow, ParsedList, scoped_candidate_key
from app.sources.fetcher import FetchResult
from app.sources.registry import Adapter, Attestation, Registry

URL='https://example.org/load'
VERSION='load-v1'


def key():
    return bytes.fromhex(os.environ['SOURCE_IDENTITY_KEY'])


def load_registry():
    body=b'load stand'
    digest=hashlib.sha256(body).hexdigest()
    proof=Attestation(passport='backend/tests/fixtures/synthetic-passport.md',fixture='backend/tests/fixtures/synthetic-source.txt',
                      fixture_sha256=digest,original_sha256=digest,source_url=URL,year=2026,kind='live',sample_rows=3,checked_rows=3,
                      verified_at=datetime(2026,11,1,tzinfo=timezone.utc),adapter_version=VERSION)
    return Registry((Adapter(VERSION,frozenset({'example.org'}),lambda response,binding:None,attested=True,attestation=proof),))


def rows_list(binding,count,seats,round_number=0):
    entries=[]
    for index in range(1,count+1):
        consent=None if index%3==0 else (index+round_number)%2==0
        entries.append(CandidateRow(candidate_key=scoped_candidate_key(binding,f'LOAD-{index:06}',key()),row_ref=f'row-{index}',official_rank=index,
                                    score=Decimal(300-index%200),consent=consent,participation='active'))
    return ParsedList(source_id=binding.source_id,group_id=binding.group_id,year=binding.year,adapter_version=binding.adapter_version,kind=binding.kind,
                      complete=True,expected_rows=count,seats=seats,entries=tuple(entries))


def raw_for(round_number,at):
    body=f'synthetic load round {round_number}'.encode()
    return FetchResult(URL,body,'text/plain',hashlib.sha256(body).hexdigest(),at,'utf-8')
