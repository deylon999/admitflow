"""Independently review official sectioned competition pages.

Only synthetic candidate fixtures, public group metadata, hashes and aggregate
audit counts leave the private cache. Publishing a profile does not enable it.
"""
from datetime import datetime
from decimal import Decimal
import hashlib
import hmac
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import secrets
import sys
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from bs4 import BeautifulSoup
from app.sources.contracts import SourceBinding
from app.sources.fetcher import FetchResult
from app.sources.table_family import SECTION_VERSION,clean,parse_table,section_metadata
from app.sources.table_profiles import build_profiles
from app.sources.profile_catalog import active_catalog,read_profile_data,publish_profile_data

GROUP_SELECTOR='#vikon-content-abitur p:-soup-contains("Название группы конкурсов:")'
DATE_SELECTOR='#vikon-content-abitur .actual-date-count-students'
INSTITUTIONS={
    '1881':('МИЭПП — Московский институт экономики, политики и права','www.miepl.ru'),
    '110420':('Уральский институт фондового рынка','uifr.ru'),
}


class IndependentSections(HTMLParser):
    def __init__(self):
        super().__init__();self.tables=[];self.depth=0;self.target=None;self.cell=None;self.parts=[];self.row=[];self.sections=[];self.metadata=[];self.meta=False
    def handle_starttag(self,tag,attrs):
        fields=dict(attrs)
        if tag=='table':
            self.depth+=1
            if 'table-scroll-thead' in fields.get('class','').split():
                if self.target is not None:raise ValueError('nested candidate table')
                self.target=self.depth;self.tables=[]
        if tag=='tr' and self.target==self.depth:self.row=[]
        if tag=='td' and self.target==self.depth:self.cell=True;self.parts=[]
        if tag=='tr' and self.target is None and 'tr-accordion' in fields.get('class','').split():self.meta=True;self.metadata=[]
    def handle_data(self,text):
        if self.cell and self.target==self.depth:self.parts.append(text)
        if self.meta:self.metadata.append(text)
    def handle_endtag(self,tag):
        if tag=='td' and self.cell and self.target==self.depth:self.row.append(' '.join(' '.join(self.parts).split()));self.cell=None
        if tag=='tr' and self.target==self.depth:
            if self.row:self.tables.append(self.row)
        if tag=='tr' and self.meta:self.meta=False
        if tag=='table':
            if self.target==self.depth:
                text=re.sub(r'^(?:Показать|Скрыть)\s*','',' '.join(' '.join(self.metadata).split()))
                self.sections.append(dict(metadata=text,rows=self.tables));self.target=None
            self.depth-=1


def compare_rows(raw,profile,parsed,secret):
    independent=IndependentSections();independent.feed(raw.decode('utf-8'))
    if len(independent.sections)!=profile.section_count:raise ValueError('independent section count')
    section=independent.sections[profile.section_index]
    if section['metadata']!=profile.section_metadata or len(section['rows'])!=profile.rows:raise ValueError('independent metadata/count')
    for i,(cells,actual) in enumerate(zip(section['rows'],parsed.entries,strict=True),1):
        if len(cells)!=profile.cell_count or cells[0]!=str(i):raise ValueError('independent order/columns')
        public_id=cells[1]
        payload=json.dumps([profile.source_id,profile.group_id,profile.year,public_id],ensure_ascii=False,separators=(',',':'))
        key=hmac.new(secret,payload.encode(),hashlib.sha256).hexdigest()
        priority=int(cells[-2]);priority=priority if priority>0 else None
        expected=(i,key,Decimal(cells[2].replace(',','.')),None,priority,'unknown')
        observed=(actual.official_rank,actual.candidate_key,actual.score,actual.consent,actual.priority,actual.participation)
        if expected!=observed:raise ValueError('independent candidate field mismatch')
    return profile.rows


def _synthetic_fixture(group_text,date_text,sections):
    output=['<!-- SYNTHETIC CANDIDATE VALUES; public reviewed group metadata only; not original HTML -->',
        '<html><body><div id="vikon-content-abitur"><p>'+escape(group_text)+'</p>',
        '<span class="actual-date-count-students">'+escape(date_text)+'</span><table class="layout"><tbody>']
    for section in sections:
        output.append('<tr class="tr-accordion"><td>'+escape(section['metadata'])+'</td></tr><tr class="tr-table-applicant"><td><table class="table-scroll-thead"><thead>')
        for row in section['header_rows']:
            output.append('<tr>'+''.join('<th rowspan="'+str(span[0])+'" colspan="'+str(span[1])+'">'+escape(label)+'</th>' for label,span in row)+'</tr>')
        output.append('</thead><tbody>')
        for i in range(1,section['rows']+1):
            values=['---']*section['cell_count'];values[0]=str(i);values[1]=f'FIXTURE-{i:06d}';values[2]=str(300-i%100)
            values[-3]='Да' if i%2 else 'Нет';values[-2]=str(0 if i%5==0 else i%3+1);values[-1]='Нет'
            output.append('<tr>'+''.join('<td>'+escape(v)+'</td>' for v in values)+'</tr>')
        output.append('</tbody></table></td></tr>')
    output.append('</tbody></table></div></body></html>')
    return ('\n'.join(output)+'\n').encode()


def main():
    report=json.loads((ROOT/'docs/sources/format-families.json').read_text(encoding='utf-8'))
    cache=ROOT/'backend/var/research/admissions-pages';root=ROOT/'backend/app/sources/profiles'
    data=read_profile_data(active_catalog(root));pending={};artifacts={};audits=[];unsupported=[];secret=secrets.token_bytes(32)
    for page in report['supplementPages']:
        ident=next((v for v in page['registryIds'] if v in INSTITUTIONS),None)
        if ident is None:continue
        body=(cache/page['bodyFile']).read_bytes()
        if hashlib.sha256(body).hexdigest()!=page['payloadHash']:raise ValueError('private original hash mismatch')
        soup=BeautifulSoup(body.decode(page.get('charset') or 'utf-8'),'html.parser');nodes=soup.select('tr.tr-table-applicant')
        if not nodes:unsupported.append(dict(url=page['requestedUrl'],code='no_section_table'));continue
        group_nodes=soup.select(GROUP_SELECTOR);date_nodes=soup.select(DATE_SELECTOR)
        if len(group_nodes)!=1 or len(date_nodes)!=1:raise ValueError('ambiguous group/date metadata')
        group_text=clean(group_nodes[0].get_text(' ',strip=True));date_text=clean(date_nodes[0].get_text(' ',strip=True))
        if not re.search(r'\b2026\s*г\.',date_text):raise ValueError('unverified archive year')
        independent=IndependentSections();independent.feed(body.decode('utf-8'))
        if len(independent.sections)!=len(nodes):raise ValueError('independent table count')
        sections=[]
        for i,node in enumerate(nodes):
            table=node.select_one('table.table-scroll-thead');previous=node.find_previous_sibling('tr')
            if table is None or previous is None or 'tr-accordion' not in previous.get('class',[]):raise ValueError('section metadata shape')
            metadata=section_metadata(previous)
            match=re.fullmatch(r'Форма обучения:\s*(.*?)\s*Источник финансирования:\s*(.*?)\s*Количество мест на прием:\s*([0-9]+)',metadata)
            if match is None or match[2]!='С оплатой обучения':raise ValueError('unreviewed funding/metadata')
            form={'Очная':'full-time','Заочная':'part-time','Очно-заочная':'mixed'}.get(match[1])
            if not form:raise ValueError('unreviewed study form')
            rows=[r for r in table.select('tr') if r.find_parent('table') is table and r.find_all('td',recursive=False)]
            if not rows or any(not row.find_all('td',recursive=False)[0].get_text(strip=True).isdigit() for row in rows):
                unsupported.append(dict(url=page['requestedUrl'],section=i,code='unconfirmed_empty_or_nonordinal_rows'));continue
            count=len(rows);width=len(rows[0].find_all('td',recursive=False))
            if any(len(r.find_all('td',recursive=False))!=width for r in rows):raise ValueError('inconsistent cells')
            headers=[clean(h.get_text(' ',strip=True)) for h in table.select('th')]
            spans=[(int(h.get('rowspan',1)),int(h.get('colspan',1))) for h in table.select('th')]
            if not headers[:3]==['№','Уникальный код поступающего','Конкурсные баллы']:raise ValueError('unreviewed candidate schema')
            header_rows=[]
            for tr in table.select('tr'):
                cells=tr.find_all('th',recursive=False)
                if cells:header_rows.append([(clean(h.get_text(' ',strip=True)),(int(h.get('rowspan',1)),int(h.get('colspan',1)))) for h in cells])
            sections.append(dict(index=i,metadata=metadata,rows=count,cell_count=width,headers=headers,header_spans=spans,
                header_rows=header_rows,seats=int(match[3]),study_form=form))
        if not sections:continue
        if len(sections)!=len(nodes):raise ValueError('mixed unknown sections need separate review')
        official_id=re.search(r'_([0-9]+)\.html$',page['requestedUrl']).group(1)
        fixture_name=f'backend/tests/fixtures/sectioned-competition/{ident}-{official_id}.html'
        fixture=_synthetic_fixture(group_text,date_text,sections);page_rows=sum(s['rows'] for s in sections)
        proof=dict(passport='docs/sources/sectioned-competition.md',fixture=fixture_name,fixture_sha256=hashlib.sha256(fixture).hexdigest(),
            original_sha256=page['payloadHash'],source_url=page.get('finalUrl',page['requestedUrl']),year=2026,kind='archive',
            sample_rows=page_rows,checked_rows=page_rows,verified_at=page['checkedAt'],adapter_version=SECTION_VERSION)
        page_scopes=[]
        for section in sections:
            name=f'section-{ident}-{official_id}-{section["index"]}-2026'
            profile=dict(source_id=name,group_id=name,url=proof['source_url'],year=2026,rows=section['rows'],seats=section['seats'],
                table_selector='table.table-scroll-thead',row_selector='tr:has(td)',columns=[['rank',0],['code',1],['score',2],['priority',section['cell_count']-2]],
                cell_count=section['cell_count'],headers=section['headers'],cell_labels=[],identity=[[GROUP_SELECTOR,group_text],[DATE_SELECTOR,date_text]],
                proof=proof,kind='archive',season_pattern=r'\b([0-9]{4})\s*г\.',season_selector=DATE_SELECTOR,
                version=SECTION_VERSION,section_selector='tr.tr-table-applicant',section_index=section['index'],section_count=len(nodes),
                section_metadata=section['metadata'],zero_priority_unknown=True,header_spans=[list(pair) for pair in section['header_spans']],
                catalog=[['university_id','miccedu-'+ident],['university_name',INSTITUTIONS[ident][0]],['university_url','https://'+INSTITUTIONS[ident][1]+'/'],
                         ['campaign_id',f'miccedu-{ident}-2026-bachelor'],['level','bachelor'],['official_id',official_id+'-'+str(section['index'])],
                         ['title',(group_text.removeprefix('Название группы конкурсов:').strip()+' · '+section['study_form'])[:290]],['study_form',section['study_form']],['funding','contract'],['category','general']])
            obj=build_profiles(dict(format='reviewed-table-profiles-v1',profiles={name:profile}))[name]
            binding=SourceBinding(name,name,2026,obj.url,urlsplit(obj.url).hostname,SECTION_VERSION,'archive',True)
            raw=FetchResult(obj.url,body,'text/html',page['payloadHash'],datetime.fromisoformat(page['checkedAt']),'utf-8')
            parsed=parse_table(raw,binding,secret,obj);compare_rows(body,obj,parsed,secret)
            synthetic=FetchResult(obj.url,fixture,'text/html',proof['fixture_sha256'],raw.fetched_at,'utf-8')
            if len(parse_table(synthetic,binding,secret,obj).entries)!=section['rows']:raise ValueError('synthetic shape mismatch')
            if name in data['profiles'] and data['profiles'][name]!=profile:raise ValueError('reviewed scope immutable')
            pending[name]=profile;page_scopes.append(dict(sourceId=name,rows=section['rows'],seats=section['seats'],studyForm=section['study_form']))
        artifacts[fixture_name]=fixture
        audits.append(dict(url=proof['source_url'],registryId=ident,originalSha256=page['payloadHash'],checkedRows=page_rows,
            sectionCount=len(nodes),scopes=page_scopes,fixtureSha256=proof['fixture_sha256'],allCandidateValuesSynthetic=True,
            independentParser='stdlib.HTMLParser',comparedFields=['rank','scoped_identity','score','unknown_consent','priority_or_null','unknown_participation']))
    if len({a['registryId'] for a in audits})<2:raise ValueError('two independently reviewed institutions required')
    for path,body in artifacts.items():target=ROOT/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(body)
    publish_profile_data({**data['profiles'],**pending},root)
    result=dict(format='sectioned-family-audit-v1',version=SECTION_VERSION,universities=2,reviewedPages=len(audits),
        reviewedScopes=len(pending),checkedRows=sum(a['checkedRows'] for a in audits),pages=audits,unsupported=unsupported,
        realSourceRowsExported=False,automaticEnable=False,kind='archive')
    (ROOT/'docs/evidence/b15-section-family-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('pages','unsupported')}))


if __name__=='__main__':main()
