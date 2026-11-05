import importlib.util
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location('source_inventory',Path(__file__).resolve().parents[2]/'scripts/source_inventory.py')
inventory=importlib.util.module_from_spec(spec);spec.loader.exec_module(inventory)


def test_discovery_keeps_navigation_and_format_evidence_without_fetching_candidate_links():
    result=inventory.discover('''<html><script src="/bitrix/core.js"></script>
    <a href="/priem/list.pdf">Конкурсные списки</a><a href="https://admit.example/priem">Поступающим</a>
    <a href="/priem?candidate=123">Личная запись</a><a href="javascript:alert(1)">Приём</a></html>'''.encode(),'https://example.edu/')
    assert {r['url'] for r in result['links']}=={'https://example.edu/priem/list.pdf','https://admit.example/priem'}
    assert set(result['formatHints'])=={'bitrix-assets','pdf-links'}
    assert next(r for r in result['links'] if r['external'])['url']=='https://admit.example/priem'


def test_site_observation_refuses_private_network_before_http(tmp_path,monkeypatch):
    monkeypatch.setattr(inventory.Fetcher,'_target',lambda *_: (_ for _ in ()).throw(inventory.FetchError('non_public_address')))
    report=inventory.observe('https://private.example/',tmp_path)
    assert report['state']=='unavailable' and report['error']=='non_public_address'
    assert report['supported'] is False
    monkeypatch.setattr(inventory.Fetcher,'_target',lambda *_: pytest.fail('cached repeat must not resolve or fetch'))
    assert inventory.observe('https://private.example/',tmp_path)==report


def test_encoding_and_port_unknowns_do_not_imply_supported_format():
    assert inventory.discover(b'hello','https://example.edu/',charset='unknown')['formatHints']==['unknown-encoding']
    with pytest.raises(ValueError):inventory.target('https://example.edu:8080/')
    assert inventory.target('http://example.edu/')=='https://example.edu/'
