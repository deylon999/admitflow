from dataclasses import replace
import hashlib
from pathlib import Path

import pytest

from app.sources.adapters.sgu2026 import GROUP_ID, SOURCE_ID, URL, VERSION, make_adapter
from app.sources.contracts import AdapterError, SourceBinding
from app.sources.fetcher import FetchResult
from app.sources.registry import Registry
from source_helpers import NOW

FIXTURE = Path(__file__).parent/'fixtures/sgu-2026/sgu-4588-derived.html'
BINDING = SourceBinding(SOURCE_ID,GROUP_ID,2026,URL,'www.sgu.ru',VERSION,'archive',True)
KEY = b'synthetic-test-only-source-key-0001'


def response(body=None):
    body = FIXTURE.read_bytes() if body is None else body
    return FetchResult(URL,body,'text/html',hashlib.sha256(body).hexdigest(),NOW,'utf-8')


def test_attested_sgu_archive_has_exact_scope_provenance_and573_rows():
    adapter=make_adapter(KEY)
    assert Registry((adapter,)).resolve(BINDING) is adapter
    parsed=adapter.parse(response(),BINDING)
    assert parsed.expected_rows == len(parsed.entries) == 573 and parsed.seats == 16
    assert parsed.kind=='archive' and parsed.year==2026 and parsed.source_updated_at is None
    assert sum(row.consent is True for row in parsed.entries)==165
    assert sum(row.consent is False for row in parsed.entries)==408
    assert sum(row.participation=='enrolled' for row in parsed.entries)==16
    assert sum(row.participation=='unknown' for row in parsed.entries)==557
    assert len({row.candidate_key for row in parsed.entries})==573
    assert [row.official_rank for row in parsed.entries]==list(range(1,574))
    assert 'FIXTURE-' not in repr(parsed)
    root=Path(__file__).resolve().parents[2]
    assert (root/adapter.attestation.passport).is_file()
    assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest()==adapter.attestation.fixture_sha256


@pytest.mark.parametrize('changes',[{'year':2027},{'kind':'live'},{'url':URL+'?another=1'},{'group_id':'other-group'},{'source_id':'other-source'}])
def test_unverified_binding_is_refused(changes):
    with pytest.raises(AdapterError,match='invalid_binding'):
        make_adapter(KEY).parse(response(),replace(BINDING,**changes))


def test_unknown_consent_priority_remain_null_and_do_not_become_negative_or_zero():
    from bs4 import BeautifulSoup
    soup=BeautifulSoup(FIXTURE.read_bytes(),'html.parser')
    soup.select_one('td[data-label="Согласие на зачисление"]').string='---'
    soup.select_one('td[data-label="Приоритет / ОВП / ВПП"]').string='---'
    parsed=make_adapter(KEY).parse(response(str(soup).encode()),BINDING)
    assert parsed.entries[0].consent is None and parsed.entries[0].priority is None
    assert 'unknown_consent' in parsed.warnings and 'unknown_priority' in parsed.warnings


@pytest.mark.parametrize('change',['year','seats','headers','truncated','duplicate','missing-row','status'])
def test_changed_schema_identity_and_partial_pages_fail_closed(change):
    from bs4 import BeautifulSoup
    soup=BeautifulSoup(FIXTURE.read_bytes(),'html.parser')
    if change=='year':
        node=soup.find(string=lambda s:s and 'Приём 2026' in s);node.replace_with('Приём 2027')
    elif change=='seats':
        node=soup.select_one('.svodka-table__info-title:-soup-contains("Бюджетных мест")').find_next_sibling();node.string='999'
    elif change=='headers':soup.select_one('table.svodka-table th').string='Other order'
    elif change=='duplicate':
        codes=soup.select('td[data-label="Код поступающего"]');codes[1].string=codes[0].get_text()
    elif change=='missing-row':soup.select_one('td[data-label="Код поступающего"]').parent.decompose()
    elif change=='status':soup.select_one('td[data-label="Статус зачисления"]').string='Unexpected state'
    body=str(soup).encode()
    if change=='truncated':body=body[:-100]
    with pytest.raises(AdapterError):make_adapter(KEY).parse(response(body),BINDING)


def test_operator_key_is_explicit_stable_and_never_rendered(monkeypatch):
    from app.sources.registry import runtime_registry
    monkeypatch.delenv('SOURCE_IDENTITY_KEY',raising=False)
    assert runtime_registry().attested_versions==()
    monkeypatch.setenv('SOURCE_IDENTITY_KEY',KEY.hex())
    adapter=runtime_registry().resolve(BINDING)
    assert KEY.hex() not in repr(adapter) and repr(KEY) not in repr(adapter)
    assert adapter.parse(response(),BINDING).entries==make_adapter(KEY).parse(response(),BINDING).entries
    monkeypatch.setenv('SOURCE_IDENTITY_KEY','private-invalid-value')
    with pytest.raises(RuntimeError,match='SOURCE_IDENTITY_KEY') as error:runtime_registry()
    assert 'private-invalid-value' not in str(error.value)
