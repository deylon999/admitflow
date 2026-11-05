"""Bounded discovery of public admissions links on official university home pages.

This never downloads candidate lists, registers sources, or enables workers.
Cached observation reports allow an identical offline repeat.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import threading
import time
from urllib.parse import quote,urljoin,urlsplit,urlunsplit
from urllib.robotparser import RobotFileParser

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from bs4 import BeautifulSoup
from app.national_catalog import load_catalog,valid_url
from app.sources.fetcher import Fetcher,FetchPolicy,FetchError
from app.sources.navigation import admissions_link_score

KEYWORDS=re.compile(r'абитур|поступ|при[её]м|конкурс|списк|admission|abitur|priem|postup|rating',re.I)
LOCKS={};GUARD=threading.Lock()


def target(site):
    parts=urlsplit(site)
    host=(parts.hostname or '').encode('idna').decode('ascii').lower()
    if parts.port not in (None,80,443): raise ValueError('unsupported port')
    return urlunsplit(('https',host,quote(parts.path or '/',safe='/%:@-._~!$&()*+,;='),quote(parts.query,safe='=&%/?:@-._~'),''))


def discover(body,url,charset=None):
    charset=(charset or 'utf-8').lower()
    if charset not in ('utf-8','utf8','windows-1251','cp1251'): return dict(links=[],formatHints=['unknown-encoding'])
    try: text=body.decode(charset)
    except UnicodeError:
        try:text=body.decode('cp1251')
        except UnicodeError:return dict(links=[],formatHints=['unknown-encoding'])
    doc=BeautifulSoup(text,'html.parser')
    links={}
    for a in doc.select('a[href]'):
        label=a.get_text(' ',strip=True)
        href=urljoin(url,a['href'])
        if not KEYWORDS.search(label+' '+href):continue
        try:valid_url(href)
        except ValueError:continue
        # Navigation links only; never export per-person query parameters.
        if re.search(r'(snils|passport|candidate|person|code|token|email)=',urlsplit(href).query,re.I):continue
        links[href]=dict(url=href,label=label[:180],external=urlsplit(href).hostname!=urlsplit(url).hostname)
    ordered=sorted(links.values(),key=lambda item:(-admissions_link_score(item['url'],item['label']),not bool(re.search(r'конкурс|списк|rating',item['label']+' '+item['url'],re.I)),item['url']))[:40]
    hints=[]
    if doc.select('script[src*="/bitrix/"] , link[href*="/bitrix/"]'):hints.append('bitrix-assets')
    if doc.select('#__next, script#__NEXT_DATA__, #app, #root'):hints.append('javascript-shell')
    if any(urlsplit(a['url']).path.lower().endswith('.pdf') for a in ordered):hints.append('pdf-links')
    if any(urlsplit(a['url']).path.lower().endswith(('.xlsx','.xls','.csv')) for a in ordered):hints.append('spreadsheet-links')
    return dict(links=ordered,formatHints=hints or ['unknown'])


def observe(url,cache,*,retain_body=False):
    key=hashlib.sha256(url.encode()).hexdigest()
    path=cache/(key+'.json')
    if path.exists():
        data=json.loads(path.read_text(encoding='utf-8'))
        if data['requestedUrl']!=url:raise ValueError('cache mismatch')
        return data
    host=urlsplit(url).hostname
    with GUARD:lock=LOCKS.setdefault(host,threading.Lock())
    result=dict(requestedUrl=url,checkedAt=datetime.now(timezone.utc).isoformat(),state='unavailable',error=None,links=[],formatHints=['unknown'],robotsState='unknown',supported=False)
    allowed={host}
    if host.startswith('www.'):allowed.add(host[4:])
    else:allowed.add('www.'+host)
    try:
        policy=FetchPolicy(domains=frozenset(allowed),max_bytes=2*1024*1024,timeout=5,max_redirects=2)
        fetcher=Fetcher(policy)
        with lock:
            try:
                robots=fetcher.fetch(urlunsplit(('https',host,'/robots.txt','','')))
                if robots.content_type=='text/plain':
                    rules=RobotFileParser();rules.parse(robots.body.decode('utf-8',errors='replace').splitlines())
                    result['robotsState']='allowed' if rules.can_fetch('AdmitFlow/0.2',url) else 'disallowed'
            except FetchError:pass
            if result['robotsState']=='disallowed':
                result.update(state='robots_disallowed',error='robots_disallowed')
            else:
                time.sleep(1)
                response=fetcher.fetch(url)
                if retain_body:
                    (cache/(response.payload_hash+'.body')).write_bytes(response.body)
                    result.update(bodyFile=response.payload_hash+'.body',charset=response.charset)
                result.update(state='discovered' if response.content_type=='text/html' else 'not_html',finalUrl=response.url,
                    payloadHash=response.payload_hash,contentType=response.content_type,
                    **(discover(response.body,response.url,response.charset) if response.content_type=='text/html' else {}))
                if result['state']=='discovered' and not result['links']:result['state']='no_links_found'
    except FetchError as error:result['error']=error.code
    except (ValueError,UnicodeError):result['error']='invalid_site'
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--limit',type=int,default=0,help='0 scans all catalog entries')
    parser.add_argument('--workers',type=int,choices=range(1,9),default=6)
    parser.add_argument('--cache',type=Path,default=ROOT/'backend/var/research/inventory')
    parser.add_argument('--output',type=Path,default=ROOT/'docs/sources/national-inventory.json')
    args=parser.parse_args();args.cache.mkdir(parents=True,exist_ok=True)
    snapshot=load_catalog();rows=snapshot.institutions[:args.limit or None]
    requests={};unresolved=[]
    for row in rows:
        if not row.official_url:
            unresolved.append(dict(registryId=row.registry_id,state='unknown_site',supported=False));continue
        try:url=target(row.official_url)
        except (ValueError,UnicodeError):
            unresolved.append(dict(registryId=row.registry_id,state='invalid_site',supported=False));continue
        requests.setdefault(url,[]).append(row.registry_id)
    observations={}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures={pool.submit(observe,url,args.cache):url for url in requests}
        for i,future in enumerate(as_completed(futures)):
            url=futures[future];observations[url]=future.result()
            if (i+1)%25==0:print(f'pages {i+1}/{len(requests)}',flush=True)
    results=list(unresolved)
    for url,ids in requests.items():
        results.extend(dict(registryId=ident,**observations[url]) for ident in ids)
    report=dict(format='admitflow-source-inventory-v1',catalogSha256=snapshot.sha256,edition=snapshot.edition,
        checkedEntries=len(rows),catalogEntries=len(snapshot.institutions),uniquePages=len(requests),
        generatedAt=max((r['checkedAt'] for r in observations.values()),default=snapshot.captured_at.isoformat()),
        counts=dict(Counter(r['state'] for r in results)),supportedSourcesAdded=0,
        limits=dict(workers=args.workers,perHostConcurrent=1,perHostPauseSeconds=1,timeoutSeconds=5,maxBytes=2*1024*1024),
        institutions=sorted(results,key=lambda r:r['registryId']))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    tmp=args.output.with_suffix('.json.tmp');tmp.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');tmp.replace(args.output)
    print(json.dumps({k:v for k,v in report.items() if k!='institutions'}),flush=True)


if __name__=='__main__':main()
