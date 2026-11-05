import copy
from dataclasses import replace
from datetime import datetime,timezone
import hashlib,json
from pathlib import Path

from bs4 import BeautifulSoup
import pytest
from app.sources.contracts import AdapterError,SourceBinding
from app.sources.fetcher import FetchResult
from app.sources.table_family import FILTERED_VERSION,TableProfile,parse_table

ROOT=Path(__file__).resolve().parents[2]
RAW_PROFILE=json.loads((ROOT/'docs/sources/bgu2026-scope.json').read_text(encoding='utf-8'))['profile']
BODY=(ROOT/'backend/tests/fixtures/filtered-table/bgu2026-construction.html').read_bytes()
KEY=b'synthetic-filtered-table-key-00001';NOW=datetime(2026,11,5,tzinfo=timezone.utc)


def profile():
    data=copy.deepcopy(RAW_PROFILE)
    for key in ('columns','identity','catalog','header_spans','cell_identity'):data[key]=tuple(tuple(pair) for pair in data[key])
    for key in ('headers','cell_labels','cell_classes','declared_count'):data[key]=tuple(data[key])
    return TableProfile(**data)


def binding(p):return SourceBinding(p.source_id,p.group_id,p.year,p.url,'bgu.ru',p.version,p.kind,True)
def response(body=BODY):return FetchResult(RAW_PROFILE['url'],body,'text/html',hashlib.sha256(body).hexdigest(),NOW,'utf-8')


def test_filtered_family_reads_declared_full_scope_without_personal_identifier_parts():
    p=profile();parsed=parse_table(response(),binding(p),KEY,p)
    assert len(parsed.entries)==109 and parsed.seats==20 and parsed.kind=='archive'
    assert sum(row.participation=='enrolled' for row in parsed.entries)==14
    assert all(row.consent is None and row.priority is None for row in parsed.entries)
    assert parsed.source_updated_at is None and [row.official_rank for row in parsed.entries]==list(range(1,110))
    assert '00000000000' not in parsed.model_dump_json() and '"70001"' not in parsed.model_dump_json()
    changed=BODY.replace(b'/00000000000/0000001',b'/99999999999/9999999')
    assert parse_table(response(changed),binding(p),KEY,p)==parsed
    for scope in (replace(binding(p),year=2027),replace(binding(p),kind='live'),replace(binding(p),group_id='other')):
        with pytest.raises(AdapterError):parse_table(response(),scope,KEY,p)


@pytest.mark.parametrize('damage',['filter','extra-selected','capacity','count','checkbox','roles','program','duplicate-prefix','unknown-status','span','year','pagination','truncated'])
def test_changed_filter_and_incomplete_or_ambiguous_payload_fail_closed(damage):
    p=profile();doc=BeautifulSoup(BODY,'html.parser');rows=[r for r in doc.select('#rating tr') if r.find_all('td',recursive=False)]
    if damage=='filter':doc.select_one('#DDLtypeKonkurs option[selected]')['value']='1'
    elif damage=='extra-selected':doc.select('#DDLedu option')[1]['selected']='selected'
    elif damage=='capacity':doc.select_one('#MainContent_divPlanPriem').string='Different seats'
    elif damage=='count':doc.select_one('#MainContent_divCountPeaple').string='Количество заявлений - 110 (данные на today)'
    elif damage=='checkbox':doc.select_one('#cbdogpaid')['checked']='checked'
    elif damage=='roles':rows[0].find_all('td')[6]['class']=['different-role']
    elif damage=='program':rows[0].find_all('td')[15].string='Different program'
    elif damage=='duplicate-prefix':rows[1].find_all('td')[3].select_one('span.text-secondary').string='70001/99999999999/9999999'
    elif damage=='unknown-status':rows[0].find_all('td')[3].select_one('span.text-success').string='Unknown status'
    elif damage=='span':doc.select('#rating th')[5]['colspan']='3'
    elif damage=='year':doc.title.string=doc.title.get_text().replace('2026','2027')
    elif damage=='pagination':doc.body.append(BeautifulSoup('<a rel="next">2</a>','html.parser').a)
    body=str(doc).encode() if damage!='truncated' else BODY[:len(BODY)//2]
    with pytest.raises(AdapterError):parse_table(response(body),binding(p),KEY,p)


def test_filtered_options_require_a_separate_version_and_valid_identity_policy():
    from app.sources.table_profiles import SGU
    with pytest.raises(ValueError):replace(SGU,code_selector='span')
    p=profile()
    for change in ({'public_code_pattern':r'[0-9]+'},{'declared_count':None},{'cell_classes':()},{'lookup_code_hint':''}):
        with pytest.raises(ValueError):replace(p,**change)
