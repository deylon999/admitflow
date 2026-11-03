from dataclasses import replace
from datetime import datetime
import hashlib
from pathlib import Path

import pytest

from app.sources.contracts import AdapterError
from app.sources.registry import Adapter, Registry
from source_helpers import BINDING, parsed, synthetic_attestation


def test_attested_adapter_needs_passport_and_fixture_evidence():
    with pytest.raises(ValueError, match='invalid_adapter_attestation'):
        Adapter('synthetic-v1',frozenset({'example.org'}),lambda *_:parsed(),attested=True)
    proof = synthetic_attestation()
    root = Path(__file__).resolve().parents[2]
    assert (root / proof.passport).is_file()
    assert hashlib.sha256((root / proof.fixture).read_bytes()).hexdigest() == proof.fixture_sha256
    adapter = Adapter('synthetic-v1',frozenset({'example.org'}),lambda *_:parsed(),attested=True,attestation=proof)
    registry = Registry((adapter,))
    assert registry.resolve(BINDING) is adapter
    for changes in ({'year':2027},{'kind':'live'},{'url':'https://example.org/another-group'}):
        with pytest.raises(AdapterError,match='invalid_binding'):
            registry.resolve(replace(BINDING,**changes))


@pytest.mark.parametrize('changes',[
    {'passport':'../private.md'},{'fixture':''},{'fixture':'/private/raw'},
    {'fixture_sha256':'x'*64},{'original_sha256':None},{'source_url':'http://example.org/list'},
    {'source_url':'https://example.org/list#fragment'},{'year':True},{'sample_rows':0},
    {'sample_rows':573,'checked_rows':49},{'checked_rows':4},{'verified_at':datetime(2026,11,3)},
])
def test_invalid_or_incomplete_attestation_is_rejected(changes):
    with pytest.raises(ValueError,match='invalid_adapter_attestation'):
        replace(synthetic_attestation(),**changes)


def test_large_list_requires_at_least_fifty_checked_rows_and_matches_adapter_version():
    proof = replace(synthetic_attestation(),sample_rows=573,checked_rows=50)
    with pytest.raises(ValueError,match='invalid_adapter_attestation'):
        Adapter('different-v2',frozenset({'example.org'}),lambda *_:parsed(),attested=True,attestation=proof)


def test_one_parser_can_attest_multiple_exact_sources_without_opening_the_domain():
    first=synthetic_attestation();second=replace(first,source_url='https://example.org/group-two')
    adapter=Adapter('synthetic-v1',frozenset({'example.org'}),lambda *_:parsed(),attested=True,attestations=(first,second))
    registry=Registry((adapter,))
    assert registry.resolve(BINDING) is registry.resolve(replace(BINDING,url=second.source_url)) is adapter
    assert len(adapter.proofs)==2
    for changes in [{'url':'https://example.org/unreviewed'},{'year':2027},{'kind':'live'},{'url':'https://sub.example.org/list','domain':'sub.example.org'}]:
        with pytest.raises(AdapterError,match='invalid_binding'):registry.resolve(replace(BINDING,**changes))
    for proofs in [(first,first),(first,replace(second,adapter_version='different-v2')),(first,replace(second,source_url='https://outside.example/list'))]:
        with pytest.raises(ValueError,match='invalid_adapter_attestation'):
            Adapter('synthetic-v1',frozenset({'example.org'}),lambda *_:parsed(),attested=True,attestations=proofs)
