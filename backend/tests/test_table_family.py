from dataclasses import replace
from datetime import datetime,timezone
import hashlib
from pathlib import Path
from bs4 import BeautifulSoup
import pytest
from app.sources.table_family import VERSION,parse_table
from app.sources.table_profiles import SGU,GUAP
from app.sources.contracts import AdapterError,SourceBinding
from app.sources.fetcher import FetchResult
from test_sgu_adapter import KEY,make_adapter,response as sgu_response
FIXTURES=Path(__file__).parent/'fixtures'


def binding(profile):
    return SourceBinding(profile.source_id,profile.group_id,profile.year,profile.url,profile.url.split('/')[2],VERSION,'archive',True)


def fetch(profile,body=None):
    path=FIXTURES/('sgu-2026/sgu-4588-derived.html' if profile==SGU else 'guap-2026-math/derived.html')
    body=path.read_bytes() if body is None else body
    return FetchResult(profile.url,body,'text/html',hashlib.sha256(body).hexdigest(),datetime(2026,11,3,tzinfo=timezone.utc),'utf-8')


@pytest.mark.parametrize('profile',[SGU,GUAP],ids=['sgu-labeled','guap-positional'])
def test_same_parser_handles_two_real_layout_profiles(profile):
    parsed=parse_table(fetch(profile),binding(profile),KEY,profile)
    assert len(parsed.entries)==profile.rows and parsed.seats==profile.seats and parsed.adapter_version==VERSION
    assert parsed.source_updated_at is None and parsed.kind=='archive'
    assert [x.official_rank for x in parsed.entries]==list(range(1,profile.rows+1))
    if profile==GUAP:
        assert all(x.consent is None for x in parsed.entries)
        assert sum(x.participation=='enrolled' for x in parsed.entries)==92
    else:
        from test_sgu_adapter import BINDING
        legacy=make_adapter(KEY).parse(sgu_response(),BINDING)
        assert parsed.entries==legacy.entries and parsed.seats==legacy.seats


@pytest.mark.parametrize('profile',[SGU,GUAP])
def test_profile_never_opens_an_unreviewed_binding_or_schema(profile):
    for changes in [{'source_id':'other'},{'group_id':'other'},{'year':2027},{'url':profile.url+'?other=1'},{'kind':'live'}]:
        with pytest.raises(AdapterError,match='invalid_binding'):parse_table(fetch(profile),replace(binding(profile),**changes),KEY,profile)
    soup=BeautifulSoup(fetch(profile).body,'html.parser');soup.select_one(profile.table_selector).select('tr:has(td)')[-1].decompose()
    with pytest.raises(AdapterError,match='invalid_format'):parse_table(fetch(profile,str(soup).encode()),binding(profile),KEY,profile)


def test_identical_fixture_codes_stay_source_scoped():
    a=parse_table(fetch(SGU),binding(SGU),KEY,SGU);b=parse_table(fetch(GUAP),binding(GUAP),KEY,GUAP)
    assert a.entries[0].candidate_key!=b.entries[0].candidate_key


@pytest.mark.parametrize('profile',[SGU,GUAP])
def test_conflicting_identity_and_html_season_fail_closed(profile):
    soup=BeautifulSoup(fetch(profile).body,'html.parser')
    selector=profile.identity[0][0];node=soup.select_one(selector)
    import copy
    node.insert_after(copy.deepcopy(node))
    with pytest.raises(AdapterError,match='invalid_format'):parse_table(fetch(profile,str(soup).encode()),binding(profile),KEY,profile)
    changed=fetch(profile).body.replace(b'2026',b'2027')
    with pytest.raises(AdapterError,match='invalid_format'):parse_table(fetch(profile,changed),binding(profile),KEY,profile)


@pytest.mark.parametrize('kind',['duplicate-code','unknown-status','changed-header','missing-capacity','truncated'])
def test_guap_negative_genuine_dom_variants(kind):
    body=fetch(GUAP).body
    if kind=='duplicate-code':body=body.replace(b'FIXTURE-000002',b'FIXTURE-000001')
    elif kind=='unknown-status':body=body.replace(b'FIXTURE-000001',('FIXTURE-000001 (Отказ)').encode())
    elif kind=='truncated':body=body[:len(body)//2]
    else:
        soup=BeautifulSoup(body,'html.parser')
        if kind=='changed-header':soup.select_one('th').string='New schema'
        else:next(h for h in soup.select('h3') if 'Количество мест' in h.get_text()).decompose()
        body=str(soup).encode()
    with pytest.raises(AdapterError,match='invalid_format'):parse_table(fetch(GUAP,body),binding(GUAP),KEY,GUAP)
