"""Bounded offline inspection of genuine SGU markup; no attestation or publication."""
from bs4 import BeautifulSoup

from .contracts import AdapterError

MAX_INSPECTION_BYTES = 8 * 1024 * 1024


def document(body: bytes, charset='utf-8'):
    if not isinstance(body, bytes) or not body or len(body) > MAX_INSPECTION_BYTES:
        raise AdapterError('invalid_format')
    encoding = (charset or 'utf-8').lower()
    if encoding not in ('utf-8', 'utf8', 'windows-1251', 'cp1251'):
        raise AdapterError('invalid_format')
    try:
        return BeautifulSoup(body.decode(encoding, errors='strict'), 'html.parser')
    except (UnicodeError, ValueError):
        raise AdapterError('invalid_format') from None


def sgu_structure(body: bytes):
    soup = document(body)
    tables = soup.select('table.svodka-table')
    if len(tables) != 1:
        raise AdapterError('invalid_format')
    table = tables[0]
    rows = table.select('tr:has(td[data-label="Код поступающего"])')
    if not rows or len(rows) > 100_000:
        raise AdapterError('invalid_format')
    metadata = {}
    for field in soup.select('div.svodka-table__info'):
        label, value = field.select_one('.svodka-table__info-title'), field.select_one('.svodka-table__info-name')
        if label and value:
            key = ' '.join(label.get_text(' ', strip=True).split())
            if key in metadata:
                raise AdapterError('invalid_format')
            metadata[key] = ' '.join(value.get_text(' ', strip=True).split())
    return soup, table, rows, metadata
