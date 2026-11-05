"""Prepare public, unattested BGU GET scope metadata; never export candidate values."""
import hashlib,json,re,sys
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'scripts')]
from bs4 import BeautifulSoup
from source_inventory import observe

URL='https://bgu.ru/abitur/bach/rating.aspx'
CACHE=ROOT/'backend/var/research/b17-bgu'
CODE_PATTERN=r'([0-9]{5})/[0-9]{11}/[0-9]{6,7}'
ENROLLED_PATTERN=r'Зачислен \(Приказ № [0-9]{1,4}-[0-9А-Яа-яA-Za-zЁё-]{1,12} от [0-9]{2}\.[0-9]{2}\.2026\)'
LOOKUP_HINT='Введите первые 5 цифр уникального кода до первого «/». Остальную часть кода вводить не нужно.'


def clean(value):return ' '.join(value.split())


def main():
    CACHE.mkdir(parents=True,exist_ok=True);observation=observe(URL,CACHE,retain_body=True)
    if observation['state'] not in ('discovered','no_links_found'):raise ValueError('official source unavailable')
    body=(CACHE/observation['bodyFile']).read_bytes()
    if hashlib.sha256(body).hexdigest()!=observation['payloadHash']:raise ValueError('original hash mismatch')
    doc=BeautifulSoup(body.decode('utf-8'),'html.parser');table=doc.select_one('#rating')
    if table is None:raise ValueError('missing table')
    rows=[r.find_all('td',recursive=False) for r in table.select('tr') if r.find_all('td',recursive=False)]
    if len(rows)!=109 or any(len(r)!=17 for r in rows):raise ValueError('unreviewed row shape')
    controls=[];identity=[['title',clean(doc.title.get_text(' ',strip=True))]]
    expected=[('DDLedu','3','Бакалавриат'),('DDLtypeKonkurs','5','С оплатой обучения'),('DDLformStudy','1','Очная'),('DDLCampaigns','21','Основной прием'),('DDLspecList','14629#20# "Организация строительного производства"','08.03.01 Строительство')]
    for ident,value,label in expected:
        nodes=doc.select('#'+ident+' option[selected]')
        if len(nodes)!=1 or nodes[0].get('value')!=value or clean(nodes[0].get_text(' ',strip=True))!=label:raise ValueError('different selected scope')
        controls.append(dict(id=ident,value=value,label=label))
        identity.extend([['#'+ident+' option[selected]',label],['#'+ident+' option[selected][value='+json.dumps(value,ensure_ascii=False)+']',label]])
    for ident in ('MainContent_divListHeader','MainContent_divListSpec','MainContent_divPlanPriem'):
        node=doc.select_one('#'+ident)
        if node is None or node.find('table'):raise ValueError('unsafe metadata node')
        identity.append(['#'+ident,clean(node.get_text(' ',strip=True))])
    if identity[-1][1]!='План приема (количество мест) - 20':raise ValueError('different capacity')
    checkbox=doc.select('#cbdogpaid[type="checkbox"]')
    if len(checkbox)!=1 or checkbox[0].has_attr('checked'):raise ValueError('partial paid-only view')
    identity.append(['#cbdogpaid[type="checkbox"]:not([checked])',''])
    source_count=doc.select_one('#MainContent_divCountPeaple')
    count_pattern=r'Количество заявлений - ([0-9]{1,6}) \(данные на .+\)'
    count_match=re.fullmatch(count_pattern,clean(source_count.get_text(' ',strip=True))) if source_count else None
    if not count_match or int(count_match[1])!=len(rows):raise ValueError('declared count mismatch')
    if doc.select('.pagination,.pager,a[rel="next"]') or any('Page$' in str(n.get('href','')) for n in doc.select('a')):raise ValueError('unreviewed pagination')
    codes=set();enrolled=0
    for ordinal,cells in enumerate(rows,1):
        spans=cells[3].select('span.text-secondary')
        match=re.fullmatch(CODE_PATTERN,clean(spans[0].get_text(' ',strip=True))) if len(spans)==1 else None
        if not match or match[1] in codes:raise ValueError('nonunique minimal lookup code')
        codes.add(match[1])
        if clean(cells[0].get_text())!=str(ordinal) or clean(cells[4].get_text())!=str(ordinal):raise ValueError('ranking mismatch')
        marked=cells[3].select('span.text-success')
        if len(marked)>1 or any(not re.fullmatch(ENROLLED_PATTERN,clean(n.get_text(' ',strip=True))) for n in marked):raise ValueError('unknown participation marker')
        enrolled+=bool(marked)
    headers=[clean(h.get_text(' ',strip=True)) for h in table.select('th')]
    classes=[' '.join(c.get('class',[])) for c in rows[0]]
    if any([' '.join(c.get('class',[])) for c in row]!=classes for row in rows):raise ValueError('varying cell roles')
    profile=dict(source_id='bgu-2026-080301-contract',group_id='bgu-2026-080301-contract',url=URL,year=2026,rows=109,seats=20,
        table_selector='#rating',row_selector='tr:has(td)',columns=[['rank',4],['code',3],['score',6]],cell_count=17,
        headers=headers,cell_labels=[],identity=identity,proof=None,kind='archive',season_pattern=r'в ([0-9]{4}) году',season_selector='title',
        version='reviewed-filtered-table-v1',header_spans=[[int(h.get('rowspan',1)),int(h.get('colspan',1))] for h in table.select('th')],
        cell_classes=classes,code_selector='span.text-secondary',public_code_pattern=CODE_PATTERN,enrolled_selector='span.text-success',
        enrolled_pattern=ENROLLED_PATTERN,declared_count=['#MainContent_divCountPeaple',count_pattern],lookup_code_hint=LOOKUP_HINT,
        catalog=[['university_id','miccedu-12'],['university_name','БГУ — Байкальский государственный университет'],['university_url','https://bgu.ru/'],
            ['campaign_id','miccedu-12-2026-bachelor'],['level','bachelor'],['official_id','14629-contract-full-time'],
            ['title','08.03.01 Строительство — Организация строительного производства, платный конкурс'],['study_form','full-time'],['funding','contract'],['category','general']])
    report=dict(format='admitflow-unattested-filtered-scope-v1',url=URL,checkedAt=observation['checkedAt'],originalSha256=observation['payloadHash'],
        robotsState=observation['robotsState'],controls=controls,declaredRows=109,seats=20,minimalLookupCodesUnique=109,
        explicitEnrolled= enrolled,consent='unknown',priority='unknown',sourceTimestamp='unknown_timezone',
        normalizesOnlyFirstCodeSegment=True,otherIdentifierPartsExported=False,attested=False,automaticEnable=False,profile=profile)
    (ROOT/'docs/sources/bgu2026-scope.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('controls','profile')}))


if __name__=='__main__':main()
