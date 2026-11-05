"""Second-stage navigation inventory, with private original-page cache.

Only bounded official-navigation candidates are fetched; list-shaped pages are
recorded as unverified, without exporting any candidate row values.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor,as_completed
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'scripts')]
from bs4 import BeautifulSoup
from app.national_catalog import valid_url
from app.sources.navigation import admissions_link_score
from source_inventory import observe,target

EXCLUDED=re.compile(r'/news/|/novost|/vacanc|/press/|/smi/|замещени|при[её]м на работу|конкурс науч|конкурс работ',re.I)
LISTS=re.compile(r'конкурсн.{0,12}списк|рейтингов.{0,12}списк|ранжирован.{0,12}списк|списк.{0,15}(поступ|подавш)|/rating|/rank|/spisk|competitive',re.I)
ADMISSIONS=re.compile(r'абитуриент|поступающ|при[её]мная комисс|при[её]м.{0,8}202[5-9]|admission|abitur|priem|postup',re.I)
RESOURCES={'.pdf':'pdf','.xlsx':'xlsx','.xls':'xls','.csv':'csv','.zip':'zip'}


def choose_links(entry,limit=2):
    ranked={}
    for link in entry.get('links',[]):
        score=admissions_link_score(link['url'],link.get('label',''))
        if not score:continue
        try:
            valid_url(link['url']);url=target(link['url'])
        except (ValueError,UnicodeError):continue
        ranked[url]=max(score,ranked.get(url,0))
    return sorted(ranked,key=lambda url:(-ranked[url],len(url),url))[:limit]


def column_kind(label):
    value=' '.join(label.casefold().split())
    if 'снилс' in value:return 'snils'
    if re.search(r'код.{0,15}(поступ|абитур)|уникальн.{0,20}(номер|код)|идентификатор',value):return 'candidate-code'
    if re.search(r'сумм.{0,15}балл|балл.{0,15}сумм|конкурсн.{0,15}балл|итого.*балл|total.*score',value):return 'score'
    if 'согласи' in value:return 'consent'
    if 'оригинал' in value:return 'original-document'
    if 'приоритет' in value:return 'priority'
    if 'зачисл' in value:return 'enrollment'
    if value in ('№','n','п/п','№ п/п','номер','место','rank'):return 'rank'
    return 'other'


def inspect_page(body,charset=None):
    encoding=(charset or 'utf-8').lower()
    if encoding not in ('utf-8','utf8','windows-1251','cp1251'):return dict(listEvidence=[],pageKind='unknown-encoding')
    try:text=body.decode(encoding)
    except UnicodeError:
        try:text=body.decode('cp1251')
        except UnicodeError:return dict(listEvidence=[],pageKind='unknown-encoding')
    doc=BeautifulSoup(text,'html.parser');evidence=[]
    for table in doc.select('table')[:100]:
        headers=[' '.join(cell.get_text(' ',strip=True).casefold().split()) for cell in table.select('th')]
        if not headers:continue
        kinds=[column_kind(label) for label in headers]
        if not {'candidate-code','snils'}.intersection(kinds) or 'score' not in kinds:continue
        rows=[row for row in table.select('tr') if row.find_all('td',recursive=False)]
        evidence.append(dict(headerHash=hashlib.sha256(json.dumps(headers,ensure_ascii=False,separators=(',',':')).encode()).hexdigest(),
            columns=kinds,headerCount=len(headers),observedRows=len(rows),
            cellCounts=sorted({len(row.find_all('td',recursive=False)) for row in rows}),
            paginationDetected=bool(doc.select('.pagination,.pager,a[rel="next"]')),complete=False))
    return dict(listEvidence=evidence,pageKind='candidate-table' if evidence else 'javascript-shell' if doc.select('#app,#root,#__next,script#__NEXT_DATA__') else 'navigation-or-unknown')


def inspect_observation(url,cache):
    result=observe(url,cache,retain_body=True)
    if result.get('bodyFile'):
        name=result['bodyFile']
        if not re.fullmatch(r'[a-f0-9]{64}\.body',name):raise ValueError('invalid private cache path')
        body=(cache/name).read_bytes()
        if hashlib.sha256(body).hexdigest()!=result.get('payloadHash'):raise ValueError('private cache hash mismatch')
        if result.get('contentType')=='text/html':result={**result,**inspect_page(body,result.get('charset'))}
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=ROOT/'docs/sources/national-inventory.json')
    parser.add_argument('--output',type=Path,default=ROOT/'docs/sources/admissions-inventory.json')
    parser.add_argument('--cache',type=Path,default=ROOT/'backend/var/research/admissions-pages')
    parser.add_argument('--workers',type=int,choices=range(1,9),default=6)
    parser.add_argument('--per-institution',type=int,choices=range(1,4),default=2)
    args=parser.parse_args();args.cache.mkdir(parents=True,exist_ok=True)
    data=json.loads(args.input.read_text(encoding='utf-8'));references={};summaries=[]
    # Earlier capped navigation can omit real admissions links behind news.
    # Refresh only capped homepages with the context-aware ranking.
    capped={r['requestedUrl'] for r in data['institutions'] if len(r.get('links',[]))==40}
    refreshed={};home_cache=args.cache/'homepages';home_cache.mkdir(exist_ok=True)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        jobs={pool.submit(observe,url,home_cache,retain_body=True):url for url in capped}
        for job in as_completed(jobs):refreshed[jobs[job]]=job.result()
    print(f'capped homepages checked: {len(refreshed)}',flush=True)
    for row in data['institutions']:
        refreshed_row=refreshed.get(row.get('requestedUrl'))
        selection=refreshed_row if refreshed_row and refreshed_row.get('links') else row
        selected=choose_links(selection,args.per_institution)
        summaries.append(dict(registryId=row['registryId'],homepageState=row['state'],selectedUrls=selected,
            status='pending' if selected else 'no-selected-admissions-link',selectionSource='refreshed-capped-homepage' if selection is not row else 'initial-homepage',supported=False))
        for url in selected:references.setdefault(url,[]).append(row['registryId'])
    pages={};requests=[]
    for url in references:
        ext=Path(urlsplit(url).path).suffix.lower()
        if ext in RESOURCES:pages[url]=dict(requestedUrl=url,state='resource-reference',resourceKind=RESOURCES[ext],supported=False,listEvidence=[])
        else:requests.append(url)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        jobs={pool.submit(inspect_observation,url,args.cache):url for url in requests}
        for i,job in enumerate(as_completed(jobs)):
            url=jobs[job];pages[url]=job.result()
            if (i+1)%25==0:print(f'admissions pages {i+1}/{len(requests)}',flush=True)
    for row in summaries:
        if row['selectedUrls']:row['status']='observed'
    result=dict(format='admitflow-admissions-inventory-v1',sourceInventorySha256=hashlib.sha256(args.input.read_bytes()).hexdigest(),
        catalogSha256=data['catalogSha256'],checkedInstitutions=len(summaries),selectedInstitutions=sum(bool(r['selectedUrls']) for r in summaries),
        uniquePages=len(pages),fetchedPageTargets=len(requests),candidateTablePages=sum(bool(r.get('listEvidence')) for r in pages.values()),
        counts=dict(sorted(Counter(r['state'] for r in pages.values()).items())),supportedSourcesAdded=0,refreshedCappedHomepages=len(refreshed),
        institutions=summaries,pages=[dict(**pages[url],registryIds=references[url]) for url in sorted(pages)])
    args.output.parent.mkdir(parents=True,exist_ok=True);tmp=args.output.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');tmp.replace(args.output)
    print(json.dumps({k:v for k,v in result.items() if k not in ('institutions','pages')}),flush=True)


if __name__=='__main__':main()
