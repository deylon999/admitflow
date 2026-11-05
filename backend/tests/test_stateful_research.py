import hashlib
import importlib.util
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location('stateful_research',Path(__file__).resolve().parents[2]/'scripts/research_stateful_formats.py')
research=importlib.util.module_from_spec(spec);spec.loader.exec_module(research)


def test_hidden_values_and_candidate_rows_are_not_exported_and_paging_stays_incomplete():
    body=b'''<html><head><title>Admission 2026</title></head><body><input name="__VIEWSTATE" value="PRIVATE-STATE-TOKEN">
    <select onchange="__doPostBack('scope','')"><option value="PRIVATE-FILTER">Scope</option></select>
    <a href="javascript:__doPostBack('grid','Page$2')">2</a><table><tr><td>PRIVATE-CANDIDATE-CODE</td></tr></table></body></html>'''
    result=research.structure(body)
    assert result['webFormsState'] and result['selectPostbackCount']==1 and result['postbackPagingLinks']==1
    assert result['headingYearEvidence']==[2026] and result['complete'] is False and result['supported'] is False
    assert 'PRIVATE' not in str(result)
    assert 'paging_not_replayed' in result['remainingChecks']


def test_empty_javascript_selectors_do_not_prove_an_empty_complete_list():
    result=research.structure(b'<html><select></select><table><tr><th>Schema</th></tr></table></html>')
    assert result['selectOptionCounts']==[0] and result['complete'] is False
    assert 'empty_selectors_need_dynamic_data' in result['remainingChecks']


def test_private_original_hash_and_path_are_verified(tmp_path):
    body=b'synthetic';digest=hashlib.sha256(body).hexdigest();(tmp_path/(digest+'.body')).write_bytes(body)
    assert research.checked_body(dict(bodyFile=digest+'.body',payloadHash=digest),tmp_path)==body
    for entry in [dict(bodyFile='../outside',payloadHash=digest),dict(bodyFile=digest+'.body',payloadHash='0'*64)]:
        with pytest.raises(ValueError):research.checked_body(entry,tmp_path)
