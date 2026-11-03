#!/usr/bin/env python3
"""Derive a clearly labelled, anonymized SGU DOM fixture from private original bytes."""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from bs4 import BeautifulSoup
from app.sources.html_inspection import sgu_structure


def sanitize(body):
    soup, table, rows, metadata = sgu_structure(body)
    original_ids = {row.select_one('td[data-label="Код поступающего"]').get_text(' ', strip=True) for row in rows}
    year = soup.find(string=lambda value: value and re.fullmatch(r'При[её]м\s+2026', value.strip()))
    if year is None:
        raise ValueError('Missing verified2026 season marker')
    result = BeautifulSoup('', 'html.parser')
    outer, head, body_tag = (copy.copy(node) for node in (soup.html, soup.head, soup.body))
    for node in (outer, head, body_tag):
        node.clear()
    if soup.title:
        head.append(copy.deepcopy(soup.title))
    outer.append(head)
    outer.append(body_tag)
    result.append(outer)
    for node in [year.parent, *soup.select('div.svodka-table__info-wrap'), table]:
        if node is not None:
            body_tag.append(copy.deepcopy(node))
    identifiers = {}
    for cell in result.select('td[data-label="Код поступающего"]'):
        original = cell.get_text(' ', strip=True)
        if original not in identifiers:
            identifiers[original] = f'FIXTURE-{len(identifiers)+1:06d}'
        cell.clear()
        cell.append(identifiers[original])
    for cell in result.select('td[data-label="Другие конкурсные группы"]'):
        cell.clear()
        cell.append('Other-group popovers omitted from anonymized fixture')
    for tag in result.find_all(True):
        if tag.attrs is None:  # A previously decomposed active ancestor owned this node.
            continue
        if tag.name in ('script', 'style', 'img', 'svg'):
            tag.decompose()
            continue
        tag.attrs = {key: value for key, value in tag.attrs.items() if key in ('class', 'data-label', 'rowspan', 'colspan')}
    value = ('<!-- DERIVED ANONYMIZED DOM FIXTURE; NOT ORIGINAL HTML; archive2026; not attested -->\n' + str(result)).encode()
    text = value.decode()
    if any(identifier and identifier in text for identifier in original_ids):
        raise ValueError('Original identifier survived sanitization')
    def facts(root):
        return [[(cell.get('data-label'), cell.get_text(' ', strip=True)) for cell in row.find_all('td', recursive=False)
                 if cell.get('data-label') not in ('Код поступающего', 'Другие конкурсные группы')]
                for row in root.select('tr:has(td[data-label="Код поступающего"])')]
    if facts(table) != facts(result):
        raise ValueError('Sanitization changed non-identifier candidate facts')
    return value, len(rows), metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with args.input.open('rb') as file:
        body = file.read(8*1024*1024+1)
    value, rows, metadata = sanitize(body)
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'sgu-4588-derived.html').write_bytes(value)
    manifest = dict(format='anonymized-pilot-fixture-v1', sourceUrl='https://www.sgu.ru/svodka/4588',
                    sourceHash=hashlib.sha256(body).hexdigest(), originalBytes=len(body),
                    derivedHash=hashlib.sha256(value).hexdigest(), derivedBytes=len(value),
                    rows=rows, sourceSeason=2026, kind='archive', attested=False,
                    retrievedAt=datetime.fromtimestamp(args.input.stat().st_mtime, timezone.utc).isoformat(),
                    transformations=['DOM subset: actual metadata/budget table/candidate table',
                                     'candidate codes replaced with unrelated sequential FIXTURE IDs',
                                     'other-group popovers removed; active tags and all non-structural attributes removed'],
                    metadata=metadata)
    (args.output / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'rows': rows, 'bytes': len(value), 'attested': False}))


if __name__ == '__main__':
    main()
