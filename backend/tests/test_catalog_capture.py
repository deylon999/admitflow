"""Source-structure failures must not silently turn into valid catalogue rows."""
import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location('capture_catalog', Path(__file__).resolve().parents[2]/'scripts/capture_catalog.py')
capture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture)


def test_source_card_link_must_match_identifier_and_origin():
    region = {'id':'10001','name':'Example'}
    for href in ['inst.php?id=999','https://other.example/inst.php?id=123']:
        body = f'<td class="inst" id="123"><a href="{href}">University</a></td>'.encode()
        with pytest.raises(ValueError,match='inconsistent'):
            capture.institutions(body,region)


def test_nonparticipant_table_is_separate_from_published_cards():
    body = b'<table><td class="inst">Nonreporter</td><td class="inst" id="123" icon="_0"><a href="inst.php?id=123">Branch</a></td></table>'
    records = capture.institutions(body,{'id':'10001','name':'Example'})
    assert len(records)==1 and records[0]['isBranch'] is True
    assert records[0]['registryId']=='123'
    assert records[0]['provenanceUrl'].endswith('/2025/_vpo/inst.php?id=123')


def test_missing_index_or_detail_is_rejected_and_unknown_site_remains_unknown():
    with pytest.raises(ValueError,match='incomplete'):
        capture.regions(b'<html>Maintenance</html>')
    with pytest.raises(ValueError,match='missing'):
        capture.detail(b'<html>Maintenance</html>')
    for site in ['unknown', 'javascript:alert(1)', 'https://one.example https://two.example']:
        record=capture.detail(f'<table id="info"><tr><td>web-site</td><td>{site}</td></tr></table>'.encode())
        assert record['officialUrl'] is None
