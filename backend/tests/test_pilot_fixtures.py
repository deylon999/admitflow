import hashlib
import json
from pathlib import Path

import pytest

from app.sources.contracts import AdapterError
from app.sources.html_inspection import document, sgu_structure

FIXTURES = Path(__file__).parent / 'fixtures/sgu-2026'


def test_actual_derived_sgu_fixture_has_verified_structure_and_no_original_ids():
    body = (FIXTURES / 'sgu-4588-derived.html').read_bytes()
    manifest = json.loads((FIXTURES / 'manifest.json').read_text(encoding='utf-8'))
    assert hashlib.sha256(body).hexdigest() == manifest['derivedHash']
    soup, table, rows, metadata = sgu_structure(body)
    assert len(rows) == manifest['rows'] == 573
    assert metadata['Код:'] == '09.03.04'
    assert metadata['Бюджетных мест:'] == '16'
    codes = [cell.get_text(strip=True) for cell in table.select('td[data-label="Код поступающего"]')]
    assert codes == [f'FIXTURE-{i:06d}' for i in range(1, 574)]
    assert not soup.select('script,style,img,svg,[href],[onclick]')
    assert manifest['kind'] == 'archive' and manifest['sourceSeason'] == 2026 and manifest['attested'] is False


@pytest.mark.parametrize('body', [b'', b'<html>login required</html>', b'<table class="svodka-table"><tr><th>Changed schema</th></tr></table>', b'\xff'])
def test_missing_or_invalid_real_structure_is_refused(body):
    with pytest.raises(AdapterError, match='invalid_format'):
        sgu_structure(body)


def test_unsupported_encoding_and_research_size_are_bounded():
    with pytest.raises(AdapterError):
        document(b'<html/>', 'utf-16')
    with pytest.raises(AdapterError):
        document(b'x' * (8*1024*1024+1))
    assert 'Пример' in document('<p>Пример</p>'.encode('cp1251'), 'windows-1251').get_text()
