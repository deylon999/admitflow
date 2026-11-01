from dataclasses import replace
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.sources.contracts import AdapterError, CandidateRow, ParsedList, SourceBinding, scoped_candidate_key
from app.sources.registry import Adapter, PRODUCTION_REGISTRY, Registry


@pytest.fixture
def binding():
    return SourceBinding('source-1','group-1',2026,'https://example.org/list','example.org','synthetic-v1','archive',True)


def test_registry_defaults_to_no_supported_sources(binding):
    with pytest.raises(AdapterError, match='adapter_unavailable'):
        PRODUCTION_REGISTRY.resolve(binding)
    adapter = Adapter('synthetic-v1',frozenset({'example.org'}),lambda raw, ctx: None)
    registry = Registry((adapter,))
    with pytest.raises(AdapterError, match='unattested_adapter'):
        registry.resolve(binding)
    assert registry.resolve(binding, allow_unattested=True) is adapter
    for changed in [replace(binding, domain='evil.org'),replace(binding,url='http://example.org/list'),replace(binding,url='https://example.org:444/list')]:
        with pytest.raises(AdapterError, match='invalid_binding'):
            registry.resolve(changed,allow_unattested=True)
    with pytest.raises(AdapterError, match='source_disabled'):
        registry.resolve(replace(binding, enabled=False),allow_unattested=True)
    with pytest.raises(ValueError, match='duplicate'):
        Registry((adapter,adapter))


def test_candidate_identity_is_scoped_and_unknown_is_preserved(binding):
    secret = b'x'*32
    key = scoped_candidate_key(binding,'public-123',secret)
    assert key == scoped_candidate_key(binding,'public-123',secret)
    for changed in [replace(binding,year=2027),replace(binding,group_id='other'),replace(binding,source_id='other')]:
        assert scoped_candidate_key(changed,'public-123',secret) != key
    row = CandidateRow(candidate_key=key,row_ref='row/1',official_rank=1)
    assert row.consent is None and row.priority is None
    assert key not in repr(row)
    for body in [dict(consent='false'),dict(official_rank=True),dict(name='Personal Name')]:
        with pytest.raises(ValidationError):
            CandidateRow.model_validate(dict(candidate_key=key,row_ref='1',official_rank=1) | body)


def test_contract_rejects_naive_time_and_does_not_invent_capacity(binding):
    body = dict(source_id=binding.source_id,group_id=binding.group_id,year=2026,adapter_version='synthetic-v1',kind='archive',complete=True,entries=())
    parsed = ParsedList(**body)
    assert parsed.seats is None
    with pytest.raises(ValidationError):
        ParsedList(**body,source_updated_at=datetime(2026,1,1))
    assert ParsedList(**body,source_updated_at=datetime(2026,1,1,tzinfo=timezone.utc)).entries == ()
