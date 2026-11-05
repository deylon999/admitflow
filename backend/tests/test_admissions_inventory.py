import importlib.util
from pathlib import Path
import pytest
spec=importlib.util.spec_from_file_location('admissions_inventory',Path(__file__).resolve().parents[2]/'scripts/admissions_inventory.py')
inventory=importlib.util.module_from_spec(spec);spec.loader.exec_module(inventory)


def test_candidate_selection_prefers_lists_and_excludes_hr_and_news():
    row={'links':[{'url':'https://example.edu/news/contest','label':'Конкурс поступающих'},
                  {'url':'https://example.edu/jobs','label':'Приём на работу'},
                  {'url':'https://trudvsem.ru/ratings_education','label':'Национальный рейтинг трудоустройства'},
                  {'url':'https://example.edu/priem','label':'Поступающим'},
                  {'url':'https://example.edu/rating','label':'Конкурсные списки'}]}
    assert inventory.choose_links(row)==['https://example.edu/rating','https://example.edu/priem']


def test_structure_never_exports_candidate_values_or_claims_completeness():
    body='<table><tr><th>№</th><th>Код поступающего</th><th>Сумма баллов</th><th>Оригинал</th></tr><tr><td>1</td><td>PRIVATE-CODE</td><td>247</td><td>Да</td></tr></table><a rel="next" href="?page=2">Next</a>'.encode()
    result=inventory.inspect_page(body)
    assert result['pageKind']=='candidate-table'
    evidence=result['listEvidence'][0]
    assert evidence['columns']==['rank','candidate-code','score','original-document']
    assert evidence['paginationDetected'] and evidence['complete'] is False
    assert 'PRIVATE-CODE' not in str(result) and '247' not in str(evidence['columns'])


def test_cache_path_escape_and_body_tampering_are_refused(tmp_path,monkeypatch):
    monkeypatch.setattr(inventory,'observe',lambda *_args,**_kwargs:dict(bodyFile='../outside',payloadHash='0'*64))
    with pytest.raises(ValueError,match='cache path'):inventory.inspect_observation('https://example.edu/',tmp_path)
    name='0'*64+'.body';(tmp_path/name).write_bytes(b'tampered')
    monkeypatch.setattr(inventory,'observe',lambda *_args,**_kwargs:dict(bodyFile=name,payloadHash='0'*64))
    with pytest.raises(ValueError,match='hash mismatch'):inventory.inspect_observation('https://example.edu/',tmp_path)
