import pytest
from app.sources.registry import Adapter,Registry,PRODUCTION_REGISTRY
from app.sources.contracts import AdapterError
from source_helpers import BINDING,parsed


@pytest.mark.parametrize('changes',[
    {'attested':'false'},{'attested':1},{'version':''},{'version':'bad\nversion'},
    {'domains':{'example.org'}},{'domains':frozenset({'*.example.org'})},{'parse':None},
])
def test_malformed_adapter_never_enters_registry(changes):
    valid=dict(version='synthetic-v1',domains=frozenset({'example.org'}),parse=lambda *_:parsed(),attested=False)
    with pytest.raises(ValueError,match='invalid_adapter_declaration'):
        Adapter(**(valid|changes))


def test_explicit_attestation_required_and_production_stays_empty():
    adapter=Adapter('synthetic-v1',frozenset({'example.org'}),lambda *_:parsed())
    registry=Registry((adapter,))
    with pytest.raises(AdapterError,match='unattested_adapter'): registry.resolve(BINDING)
    assert registry.resolve(BINDING,allow_unattested=True) is adapter
    assert PRODUCTION_REGISTRY.attested_versions==()
