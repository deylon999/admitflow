from dataclasses import replace
from decimal import Decimal
import hashlib,importlib.util
from pathlib import Path

import pytest
from app.sources.contracts import AdapterError
from app.sources.registry import runtime_registry
from app.sources.table_family import FILTERED_VERSION,parse_table
from app.sources.table_profiles import PROFILES
from test_filtered_table import KEY,binding,response

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('review_bgu_scope',ROOT/'scripts/review_bgu_scope.py')
review=importlib.util.module_from_spec(spec);spec.loader.exec_module(review)
PROFILE=PROFILES['bgu-2026-080301-contract']


def test_reviewed_bgu_proof_and_registry_open_only_the_exact_get_scope(monkeypatch):
    monkeypatch.setenv('SOURCE_IDENTITY_KEY',KEY.hex());registry=runtime_registry();p=PROFILE
    assert p.version==FILTERED_VERSION and p.proof.checked_rows==p.proof.sample_rows==109
    assert hashlib.sha256((ROOT/p.proof.fixture).read_bytes()).hexdigest()==p.proof.fixture_sha256
    assert (ROOT/p.proof.passport).is_file()
    raw=response();scope=binding(p);adapter=registry.resolve(scope)
    parsed=adapter.parse(raw,scope)
    assert review.compare_rows(raw.body,p,parsed,KEY)['allFieldsMatched']
    for change in ({'url':p.url+'?id=12'},{'year':2027},{'kind':'live'},{'url':'https://bgu.ru/abitur/mag/rating.aspx'}):
        with pytest.raises(AdapterError):registry.resolve(replace(scope,**change))
    with pytest.raises(AdapterError):adapter.parse(raw,replace(scope,source_id='unknown'))


def test_independent_audit_detects_wrong_score_identity_or_seats_even_when_parser_output_is_valid():
    p=PROFILE;raw=response();parsed=parse_table(raw,binding(p),KEY,p)
    first=parsed.entries[0]
    for changed in (first.model_copy(update={'score':Decimal('1')}),first.model_copy(update={'candidate_key':'0'*64}),first.model_copy(update={'participation':'unknown'})):
        wrong=parsed.model_copy(update={'entries':(changed,*parsed.entries[1:])})
        with pytest.raises(ValueError,match='independent candidate facts mismatch'):review.compare_rows(raw.body,p,wrong,KEY)
    with pytest.raises(ValueError,match='independent capacity mismatch'):review.compare_rows(raw.body,replace(p,seats=21),parsed,KEY)
