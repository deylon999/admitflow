"""Bounded official-HTML research: stateful selectors are not complete imports.

Only provenance, hashes and aggregate structure leave the private cache. Hidden
field values, selected option values and candidate rows are never exported.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urljoin,urlsplit

ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'scripts')]
from bs4 import BeautifulSoup
from app.national_catalog import load_catalog,valid_url
from admissions_inventory import inspect_observation
from source_inventory import target


def structure(body,charset=None):
    encoding=(charset or 'utf-8').lower()
    if encoding not in ('utf-8','utf8','windows-1251','cp1251'):return dict(code='unknown_encoding',complete=False)
    try:doc=BeautifulSoup(body.decode(encoding),'html.parser')
    except UnicodeError:return dict(code='unknown_encoding',complete=False)
    stateful=bool(doc.select('input[name="__VIEWSTATE"],input[name="__EVENTVALIDATION"]'))
    selects=doc.select('select')
    paging=sum(bool(re.search(r'Page\$',str(node.get('href',''))+' '+str(node.get('onclick','')))) for node in doc.select('a,button,input'))
    postbacks=sum('__doPostBack' in str(node.get('onchange','')) for node in selects)
    headings=' '.join(node.get_text(' ',strip=True) for node in doc.select('h1,h2,h3,title'))
    years=sorted({int(y) for y in re.findall(r'\b(20[0-9]{2})\b',headings)})
    header_text=' '.join(node.get_text(' ',strip=True).casefold() for node in doc.select('th'))
    options=[len(node.select('option')) for node in selects]
    reasons=['capacity_and_scope_not_independently_verified']
    if stateful:reasons.append('webforms_state_not_replayed')
    if selects:reasons.append('filter_selection_not_replayed')
    if paging:reasons.append('paging_not_replayed')
    if any(n==0 for n in options):reasons.append('empty_selectors_need_dynamic_data')
    if 'специальная дисциплина' in header_text:reasons.append('visible_postgraduate_columns_need_separate_level_review')
    return dict(code='stateful_html_candidate' if stateful else 'dynamic_filter_candidate' if selects else 'unattested_table_candidate',
        webFormsState=stateful,selectCount=len(selects),selectOptionCounts=options,selectPostbackCount=postbacks,
        postbackPagingLinks=paging,headingYearEvidence=years,visiblePostgraduateColumns='специальная дисциплина' in header_text,
        complete=False,supported=False,remainingChecks=reasons)


def checked_body(observation,cache):
    name=observation.get('bodyFile')
    if not name:return None
    if not re.fullmatch(r'[a-f0-9]{64}\.body',name):raise ValueError('invalid private body path')
    body=(cache/name).read_bytes()
    if hashlib.sha256(body).hexdigest()!=observation.get('payloadHash'):raise ValueError('private body hash mismatch')
    return body


def summarize(observation,cache,registry_id,parent=None):
    allowed=('requestedUrl','finalUrl','checkedAt','state','error','robotsState','contentType','payloadHash')
    result={key:observation[key] for key in allowed if key in observation}
    result.update(registryId=registry_id,parent=parent,listEvidence=observation.get('listEvidence',[]),supported=False,complete=False)
    body=checked_body(observation,cache)
    if body is not None and observation.get('contentType')=='text/html':result['structure']=structure(body,observation.get('charset'))
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seeds',type=Path,default=ROOT/'docs/sources/b16-format-seeds.json')
    parser.add_argument('--inventory',type=Path,default=ROOT/'docs/sources/admissions-inventory.json')
    parser.add_argument('--cache',type=Path,default=ROOT/'backend/var/research/b16-stateful')
    parser.add_argument('--output',type=Path,default=ROOT/'docs/sources/stateful-format-research.json')
    args=parser.parse_args();args.cache.mkdir(parents=True,exist_ok=True)
    seeds=json.loads(args.seeds.read_text(encoding='utf-8'));inventory=json.loads(args.inventory.read_text(encoding='utf-8'))
    if seeds['format']!='admitflow-stateful-discovery-v1' or not 1<=len(seeds['parents'])<=10:raise ValueError('invalid research seeds')
    known={page['requestedUrl']:set(page['registryIds']) for page in inventory['pages']}
    catalog={row.registry_id:row for row in load_catalog().institutions};pages={};refused=[]
    for seed in seeds['parents']:
        url=target(seed['url']);ident=seed['registryId'];valid_url(url)
        official=catalog[ident].official_url
        if (ident not in known.get(url,set()) or not official
            or urlsplit(url).hostname.removeprefix('www.')!=urlsplit(official).hostname.removeprefix('www.')):
            raise ValueError('unverified official seed')
        if not isinstance(seed['children'],list) or len(seed['children'])>4:raise ValueError('research child bound')
        observation=inspect_observation(url,args.cache);pages[url]=summarize(observation,args.cache,ident)
        body=checked_body(observation,args.cache);linked=set()
        if body is not None:
            doc=BeautifulSoup(body.decode(observation.get('charset') or 'utf-8',errors='replace'),'html.parser')
            for node in doc.select('a[href]'):
                candidate=urljoin(observation.get('finalUrl',url),node['href'])
                try:valid_url(candidate);candidate=target(candidate)
                except (ValueError,UnicodeError):continue
                linked.add(candidate)
        for child in seed['children']:
            valid_url(child);child=target(child)
            if child not in linked or urlsplit(child).hostname!=urlsplit(url).hostname:
                refused.append(dict(registryId=ident,url=child,code='not_verified_same_host_parent_link'));continue
            if child not in pages:
                observed=inspect_observation(child,args.cache)
                pages[child]=summarize(observed,args.cache,ident,dict(url=url,payloadHash=observation.get('payloadHash')))
        print(f'official seed observed; accumulated pages={len(pages)}',flush=True)
    rows=sorted(pages.values(),key=lambda row:row['requestedUrl'])
    report=dict(format='admitflow-stateful-format-research-v1',seedsSha256=hashlib.sha256(args.seeds.read_bytes()).hexdigest(),
        inventorySha256=hashlib.sha256(args.inventory.read_bytes()).hexdigest(),pages=rows,refusedLinks=refused,
        checkedPages=len(rows),institutions=len({r['registryId'] for r in rows}),states=dict(Counter(r['state'] for r in rows)),
        limits=dict(maxParents=10,maxChildrenPerParent=4,maxBytes=2*1024*1024,timeoutSeconds=5,workers=1,postRequests=0),
        supportedSourcesAdded=0,realCandidateValuesExported=False,hiddenValuesExported=False,
        nextStep='Review exact GET/POST filter selection, paging, campaign and competition capacity before any attestation')
    args.output.parent.mkdir(parents=True,exist_ok=True);temp=args.output.with_suffix('.json.tmp')
    temp.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');temp.replace(args.output)
    print(json.dumps({key:value for key,value in report.items() if key not in ('pages','refusedLinks')}))


if __name__=='__main__':main()
