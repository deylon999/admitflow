"""Audit private SGU4576 original with independent stdlib parser.

Writes only public group metadata, aggregate evidence and synthetic test rows.
No original candidate identifier, score/consent tuple, or identity key is exported.
"""
import argparse
import copy
from datetime import datetime,timezone
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

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from bs4 import BeautifulSoup
from app.sources.contracts import SourceBinding
from app.sources.fetcher import FetchResult
from app.sources.registry import Attestation
from app.sources.table_family import TableProfile,SCHEMA_SET_VERSION,parse_table

VERSION=SCHEMA_SET_VERSION


class IndependentRows(HTMLParser):
    def __init__(self):
        super().__init__();self.depth=0;self.rows=[];self.row=None;self.cell=None;self.parts=[];self.text=[]
    def handle_starttag(self,tag,attrs):
        fields=dict(attrs)
        if tag=='table':
            if self.depth:self.depth+=1
            elif 'svodka-table' in fields.get('class','').split():self.depth=1
        elif tag=='tr' and self.depth==1:self.row={}
        elif tag=='td' and self.depth==1:self.cell=fields.get('data-label');self.parts=[]
    def handle_data(self,data):
        self.text.append(data)
        if self.depth==1 and self.cell:self.parts.append(data)
    def handle_endtag(self,tag):
        if tag=='td' and self.depth==1 and self.cell:
            if self.cell in self.row:raise ValueError('duplicate column')
            self.row[self.cell]=' '.join(' '.join(self.parts).split());self.cell=None
        elif tag=='tr' and self.depth==1:
            if self.row and 'Код поступающего' in self.row:self.rows.append(self.row)
            self.row=None
        elif tag=='table' and self.depth:self.depth-=1


def profile_object(data):
    fields=copy.deepcopy(data)
    for key in ('columns','identity','catalog'):fields[key]=tuple(tuple(pair) for pair in fields[key])
    for key in ('headers','cell_labels'):fields[key]=tuple(fields[key])
    if 'unordered_label_groups' in fields:fields['unordered_label_groups']=tuple(tuple(group) for group in fields['unordered_label_groups'])
    proof=fields['proof'];proof['verified_at']=datetime.fromisoformat(proof['verified_at']);fields['proof']=Attestation(**proof)
    return TableProfile(**fields)


def audit_rows(body,parsed,secret):
    independent=IndependentRows();independent.feed(body.decode('utf-8'))
    if independent.depth or len(independent.rows)!=len(parsed.entries):raise ValueError('independent row count failed')
    for i,(row,actual) in enumerate(zip(independent.rows,parsed.entries,strict=True),1):
        scope=json.dumps([parsed.source_id,parsed.group_id,parsed.year,row['Код поступающего']],ensure_ascii=False,separators=(',',':'))
        expected=(i,Decimal(row['Сумма баллов'].replace(',','.')),{'Да':True,'Нет':False}.get(row['Согласие на зачисление']),
                  int(row['Приоритет / ОВП / ВПП'].split('/')[0]),'enrolled' if row['Статус зачисления']=='Зачислен' else 'unknown',
                  hmac.new(secret,scope.encode(),hashlib.sha256).hexdigest())
        if row['№']!=str(i) or expected!=(actual.official_rank,actual.score,actual.consent,actual.priority,actual.participation,actual.candidate_key):
            raise ValueError('independent row audit failed')
    match=re.search(r'Бюджетных мест:\s*(\d+)',' '.join(independent.text))
    if not match or int(match[1])!=parsed.seats:raise ValueError('independent capacity failed')
    return len(parsed.entries)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path)
    args=parser.parse_args();body=args.input.read_bytes()
    if len(body)>8*1024*1024:raise ValueError('original too large')
    source='sgu-2026-4576';url='https://www.sgu.ru/svodka/4576'
    independent=IndependentRows();independent.feed(body.decode('utf-8'))
    if independent.depth or len(independent.rows)!=453:raise ValueError('unverified row count')
    seat_match=re.search(r'Бюджетных мест:\s*(\d+)',' '.join(independent.text))
    if not seat_match or int(seat_match[1])!=24:raise ValueError('unverified capacity')
    document=BeautifulSoup(body.decode('utf-8'),'html.parser');table=document.select_one('table.svodka-table')
    all_profiles=ROOT/'backend/app/sources/profiles/reviewed.json'
    data=json.loads(all_profiles.read_text(encoding='utf-8'));profile=copy.deepcopy(data['profiles']['sgu-2026-4588'])
    profile.update(source_id=source,group_id=source,url=url,rows=453,seats=24,
        version=VERSION,unordered_label_groups=[['Элементарная математика','Математика'],['Основы физики','Основы алгоритмизации и программирование','Физика','Информатика и ИКТ']],
        cell_labels=[td.get('data-label') for td in table.select_one('tr:has(td[data-label="Код поступающего"])').find_all('td',recursive=False)],
        headers=[' '.join(h.get_text(' ',strip=True).split()) for h in table.select('th')],
        identity=[['div.svodka-table__info',' '.join(h.get_text(' ',strip=True).split())] for h in document.select('div.svodka-table__info')])
    catalog=dict(profile['catalog']);catalog.update(official_id='4576',title='02.03.03 Математическое обеспечение и администрирование информационных систем — общий конкурс')
    profile['catalog']=list(map(list,catalog.items()))
    # Shape fixture: all candidate values below are newly generated synthetic data.
    markup=['<!-- SYNTHETIC CANDIDATE ROWS; genuine-reviewed public group metadata only; NOT ORIGINAL HTML -->',
            '<html><head><title>SGU4576 synthetic format fixture</title></head><body><p>Приём 2026</p>']
    markup.extend('<div class="svodka-table__info">'+escape(value)+'</div>' for _,value in profile['identity'])
    markup.append('<table class="svodka-table"><thead><tr>'+''.join('<th>'+escape(h)+'</th>' for h in profile['headers'])+'</tr></thead><tbody>')
    labels=profile['cell_labels']
    for i in range(1,454):
        values={label:'---' for label in labels}
        values.update({'№':str(i),'Код поступающего':f'FIXTURE-{i:06d}','Сумма баллов':str(300-i%120),
            'Согласие на зачисление':'Да' if i%3==0 else 'Нет','Статус зачисления':'---','Приоритет / ОВП / ВПП':f'{1+i%7} / 0 / 0'})
        markup.append('<tr>'+''.join('<td data-label="'+escape(label,quote=True)+'">'+escape(values[label])+'</td>' for label in labels)+'</tr>')
    markup.append('</tbody></table></body></html>');fixture='\n'.join(markup).encode('utf-8')
    profile['proof']=dict(passport='docs/sources/sgu-4576.md',fixture='backend/tests/fixtures/sgu-2026-4576/synthetic.html',
        fixture_sha256=hashlib.sha256(fixture).hexdigest(),original_sha256=hashlib.sha256(body).hexdigest(),source_url=url,year=2026,kind='archive',
        sample_rows=453,checked_rows=453,verified_at=datetime.fromtimestamp(args.input.stat().st_mtime,timezone.utc).isoformat(),adapter_version=VERSION)
    p=profile_object(profile);binding=SourceBinding(source,source,2026,url,'www.sgu.ru',VERSION,'archive',True)
    secret=secrets.token_bytes(32)
    raw=FetchResult(url,body,'text/html',hashlib.sha256(body).hexdigest(),datetime.now(timezone.utc),'utf-8')
    parsed=parse_table(raw,binding,secret,p)
    audit_rows(body,parsed,secret)
    synthetic=parse_table(FetchResult(url,fixture,'text/html',hashlib.sha256(fixture).hexdigest(),raw.fetched_at,'utf-8'),binding,secret,p)
    if len(synthetic.entries)!=453:raise ValueError('synthetic fixture shape failed')
    if source in data['profiles'] and data['profiles'][source]!=profile:
        raise ValueError('reviewed scope is immutable; use a new reviewed version')
    report=dict(sourceId=source,sourceUrl=url,kind='archive',year=2026,originalSha256=hashlib.sha256(body).hexdigest(),
        originalBytes=len(body),checkedRows=453,seats=24,independentParser='stdlib.HTMLParser',
        comparedFields=['official_rank','score','consent','priority','participation','scoped_identity'],
        fixtureKind='synthetic-candidate-values-with-reviewed-public-metadata',fixtureSha256=hashlib.sha256(fixture).hexdigest(),
        originalCandidateValuesExported=False,success=True)
    target=ROOT/profile['proof']['fixture'];target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(fixture)
    (ROOT/'docs/evidence/b14-sgu4576-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    data['profiles'][source]=profile;all_profiles.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report))


if __name__=='__main__':main()
