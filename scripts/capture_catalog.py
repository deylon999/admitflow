"""Capture public MICCEDU institution metadata; never fetch admissions lists.

Run with backend/.venv/Scripts/python.exe scripts/capture_catalog.py.
Cached pages stay in ignored backend/var; a repeat capture makes no requests.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.parse import parse_qs, urljoin, urlsplit
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://monitoring.miccedu.ru/'
INDEX = ORIGIN + '?m=vpo&year=2025'
BASE = ORIGIN + 'iam/2025/_vpo/'


def soup(body):
    return BeautifulSoup(body.decode('utf-8', errors='strict'), 'html.parser')


def regions(body):
    found = {}
    for link in soup(body).select('a[href*="material.php"]'):
        url = urljoin(ORIGIN, link['href'])
        parts = urlsplit(url)
        query = parse_qs(parts.query)
        if parts.netloc != 'monitoring.miccedu.ru' or parts.path != '/iam/2025/_vpo/material.php' or query.get('type') != ['2']:
            continue
        code = query.get('id', [''])[0]
        if not re.fullmatch(r'\d{5}', code):
            raise ValueError('invalid region identifier')
        found[code] = dict(id=code, name=link.get_text(' ', strip=True), url=url)
    if len(found) < 80:
        raise ValueError('incomplete index')
    return list(found.values())


def institutions(body, region):
    records = []
    for cell in soup(body).select('td.inst'):
        link = cell.select_one('a[href*="inst.php"]')
        ident = cell.get('id', '')
        if not ident and link is None:
            # Separate source table lists organisations without published cards.
            continue
        if link is None or not re.fullmatch(r'\d{1,12}', ident):
            raise ValueError('invalid institution')
        url = urljoin(BASE, link['href'])
        if urlsplit(url).netloc != 'monitoring.miccedu.ru' or parse_qs(urlsplit(url).query).get('id') != [ident]:
            raise ValueError('inconsistent institution link')
        records.append(dict(registryId=ident, name=link.get_text(' ', strip=True), region=region['name'],
                            regionId=region['id'], provenanceUrl=url, isBranch=cell.get('icon') == '_0'))
    return records


def detail(body):
    doc = soup(body)
    table = doc.select_one('table#info')
    if table is None:
        raise ValueError('missing institution details')
    site = None
    for row in table.select('tr'):
        cells = row.find_all('td', recursive=False)
        if len(cells) == 2 and cells[0].get_text(' ',strip=True).lower().startswith('web-'):
            value = cells[1].get_text(' ', strip=True)
            # Some official records have no site or list several: retain unknown.
            if re.fullmatch(r'https?://[^\s<>]+', value) and urlsplit(value).hostname:
                site = value
    parents = []
    for label in doc.find_all(string=re.compile('Сведения о головной образовательной организации')):
        node = label.parent
        for _ in range(3):
            if node is None: break
            parents = [parse_qs(urlsplit(a['href']).query).get('id', [''])[0] for a in node.select('a[href*="inst.php"]')]
            if parents: break
            node = node.parent
    return dict(officialUrl=site, parentRegistryId=parents[0] if len(parents)==1 else None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, default=ROOT/'backend/var/research/national')
    parser.add_argument('--output', type=Path, default=ROOT/'backend/app/data/national-catalog.json')
    parser.add_argument('--details', action='store_true')
    args = parser.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)
    captures = []
    def fetch(url, name):
        path = args.cache/name
        meta = path.with_suffix('.meta.json')
        if not path.exists():
            time.sleep(0.5)
            request = Request(url, headers={'User-Agent':'AdmitFlow-CatalogResearch/1.0', 'Accept':'text/html'})
            with urlopen(request, timeout=25) as response:
                if urlsplit(response.url).hostname != 'monitoring.miccedu.ru': raise ValueError('unexpected redirect')
                body = response.read(5*1024*1024+1)
                if len(body)>5*1024*1024: raise ValueError('page too large')
            path.write_bytes(body)
            meta.write_text(json.dumps(dict(url=url,fetchedAt=datetime.now(timezone.utc).isoformat())),encoding='utf-8')
        body = path.read_bytes()
        metadata = json.loads(meta.read_text(encoding='utf-8')) if meta.exists() else dict(url=url, fetchedAt=datetime.fromtimestamp(path.stat().st_mtime,timezone.utc).isoformat())
        if metadata['url'] != url: raise ValueError('cache URL mismatch')
        captures.append(dict(**metadata,file=name,sha256=hashlib.sha256(body).hexdigest()))
        return body
    index = fetch(INDEX,'miccedu-2025-index.html')
    areas = regions(index)
    records = []
    unlinked = []
    for i, area in enumerate(areas):
        body = fetch(area['url'],f"region-{area['id']}.html")
        rows = institutions(body,area)
        unlinked.extend(dict(name=c.get_text(' ',strip=True),region=area['name'],regionId=area['id'],provenanceUrl=area['url'])
                        for c in soup(body).select('td.inst') if not c.get('id') and c.select_one('a[href*="inst.php"]') is None)
        records.extend(rows)
        print(f"region {i+1}/{len(areas)}: {len(rows)} institutions",flush=True)
    ids = [r['registryId'] for r in records]
    if len(ids)!=len(set(ids)) or len(ids)<1000: raise ValueError('duplicate or incomplete institution set')
    if args.details:
        def enrich(row):
            row.update(detail(fetch(row['provenanceUrl'],f"inst-{row['registryId']}.html")))
            return row
        with ThreadPoolExecutor(max_workers=2) as pool:
            for i,_ in enumerate(pool.map(enrich,records)):
                if (i+1)%50==0: print(f'details {i+1}/{len(records)}',flush=True)
    else:
        for row in records: row.update(officialUrl=None,parentRegistryId=None)
    text=soup(index).get_text(' ',strip=True)
    count=re.search(r'(\d[\d ]*) организаций высшего образования',text)
    if not count or int(count[1].replace(' ','')) != len(records):
        raise ValueError('regional records do not match the published total')
    manifest=dict(format='miccedu-catalog-v1',sourceUrl=INDEX,edition=2025,sourceUpdatedAt='2026-02-03',
        capturedAt=max(c['fetchedAt'] for c in captures),scope='monitoring-participants',nationalTotal=None,
        headlineTotal=int(count[1].replace(' ','')),recordCount=len(records),regionCount=len(areas),
        branchCount=sum(r['isBranch'] for r in records),detailsCaptured=args.details,
        exclusions=['defence-and-security','outside-russia','non-reporting-institutions'],unlinkedInstitutions=unlinked,captures=sorted(captures,key=lambda c:c['file']),
        institutions=sorted(records,key=lambda r:r['registryId']))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in manifest.items() if k not in ('captures','institutions','unlinkedInstitutions')},ensure_ascii=True),flush=True)


if __name__=='__main__': main()
