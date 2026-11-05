"""Group observed list structures; crawl only explicitly linked seed children.

Evidence is structural and unverified. No adapter/source is registered here.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor,as_completed
import hashlib
import json
from pathlib import Path
import sys
from urllib.parse import urljoin,urlsplit

ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'scripts')]
from bs4 import BeautifulSoup
from app.national_catalog import load_catalog,valid_url
from admissions_inventory import inspect_observation
from source_inventory import target


def group_pages(pages):
    groups={}
    for page in pages:
        for table in page.get('listEvidence',[]):
            signature=(dict(kind='hierarchical-header',primaryHeaderHash=table['primaryHeaderHash'],primaryColumns=table['primaryColumns'])
                if table.get('hierarchicalHeader') else dict(kind='flat-header',columns=table['columns'],headerCount=table['headerCount'],cellCounts=table['cellCounts']))
            digest=hashlib.sha256(json.dumps(signature,sort_keys=True,separators=(',',':')).encode()).hexdigest()
            group=groups.setdefault(digest,dict(signatureId=digest,signature=signature,members=[],supported=False))
            group['members'].append(dict(url=page.get('finalUrl',page['requestedUrl']),registryIds=page['registryIds'],
                payloadHash=page.get('payloadHash'),headerHash=table['headerHash'],observedRows=table['observedRows'],
                paginationDetected=table['paginationDetected'],complete=False))
    for group in groups.values():
        group['members'].sort(key=lambda row:(row['url'],row['headerHash']))
        hosts={urlsplit(row['url']).hostname for row in group['members']}
        institutions={ident for row in group['members'] for ident in row['registryIds']}
        group.update(distinctHosts=len(hosts),distinctInstitutions=len(institutions),
            crossInstitutionCandidate=len(hosts)>=2 and len(institutions)>=2)
    return sorted(groups.values(),key=lambda group:(not group['crossInstitutionCandidate'],-group['distinctHosts'],group['signatureId']))


def seeded_children(seed,cache,catalog):
    institution=catalog.get(seed['registryId'])
    if institution is None or not institution.official_url:raise ValueError('unknown seed institution')
    url=target(seed['url']);host=urlsplit(url).hostname
    official=urlsplit(institution.official_url).hostname
    if host.removeprefix('www.')!=official.removeprefix('www.'):raise ValueError('seed is not on the recorded official host')
    parent=inspect_observation(url,cache)
    children=[]
    if parent.get('bodyFile') and parent.get('contentType')=='text/html':
        body=(cache/parent['bodyFile']).read_bytes()
        doc=BeautifulSoup(body.decode(parent.get('charset') or 'utf-8'),'html.parser')
        for link in doc.select('a[href]'):
            child=urljoin(parent.get('finalUrl',url),link['href'])
            if seed['childPathMarker'] not in urlsplit(child).path:continue
            try:valid_url(child);child=target(child)
            except (ValueError,UnicodeError):continue
            if urlsplit(child).hostname.removeprefix('www.')!=host.removeprefix('www.'):continue
            if child not in children:children.append(child)
    if len(children)>30:raise ValueError('seed child limit exceeded')
    return dict(registryId=seed['registryId'],parentUrl=url,parentPayloadHash=parent.get('payloadHash'),parentState=parent['state'],children=children)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=ROOT/'docs/sources/admissions-inventory.json')
    parser.add_argument('--seeds',type=Path,default=ROOT/'docs/sources/format-seeds.json')
    parser.add_argument('--cache',type=Path,default=ROOT/'backend/var/research/admissions-pages')
    parser.add_argument('--output',type=Path,default=ROOT/'docs/sources/format-families.json')
    args=parser.parse_args();data=json.loads(args.input.read_text(encoding='utf-8'));seeds=json.loads(args.seeds.read_text(encoding='utf-8'))
    if seeds['format']!='admitflow-reviewed-discovery-seeds-v1' or not 1<=len(seeds['parents'])<=20:raise ValueError('invalid discovery seeds')
    catalog={r.registry_id:r for r in load_catalog().institutions};parents=[];requests={}
    for seed in seeds['parents']:
        parent=seeded_children(seed,args.cache,catalog);parents.append(parent)
        for url in parent['children']:requests.setdefault(url,[]).append(parent['registryId'])
    supplements=[]
    with ThreadPoolExecutor(max_workers=3) as pool:
        jobs={pool.submit(inspect_observation,url,args.cache):url for url in requests}
        for i,job in enumerate(as_completed(jobs)):
            url=jobs[job];supplements.append(dict(**job.result(),registryIds=sorted(set(requests[url]))))
            print(f'linked original pages {i+1}/{len(requests)}',flush=True)
    supplements.sort(key=lambda r:r['requestedUrl'])
    pages={p['requestedUrl']:p for p in data['pages']}
    pages.update({p['requestedUrl']:p for p in supplements})
    groups=group_pages(pages.values())
    report=dict(format='admitflow-format-families-v1',admissionsInventorySha256=hashlib.sha256(args.input.read_bytes()).hexdigest(),
        discoverySeedsSha256=hashlib.sha256(args.seeds.read_bytes()).hexdigest(),parents=parents,supplementPages=supplements,
        supplementCount=len(supplements),supplementStates=dict(sorted(Counter(p['state'] for p in supplements).items())),
        groups=groups,crossInstitutionCandidateGroups=sum(g['crossInstitutionCandidate'] for g in groups),
        realAttestationsAdded=0,limitations=['Structural candidates only; completeness/season/capacity not yet attested','CMS and extension similarity do not establish compatibility'])
    args.output.parent.mkdir(parents=True,exist_ok=True);tmp=args.output.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');tmp.replace(args.output)
    print(json.dumps({k:v for k,v in report.items() if k not in ('parents','supplementPages','groups')}),flush=True)


if __name__=='__main__':main()
