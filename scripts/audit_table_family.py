#!/usr/bin/env python3
"""Independent stdlib row audit for the shared table decoder;aggregates only."""
import argparse
from collections import Counter
from datetime import datetime,timezone
from decimal import Decimal
import hashlib,json,re,secrets,sys
from html.parser import HTMLParser
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.sources.table_family import VERSION,parse_table
from app.sources.table_profiles import SGU,GUAP
from app.sources.contracts import SourceBinding,scoped_candidate_key
from app.sources.fetcher import FetchResult


class Rows(HTMLParser):
    def __init__(self):super().__init__();self.depth=0;self.row=None;self.cells=[];self.parts=None;self.rows=[]
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='table':
            if self.depth:self.depth+=1
            elif 'pk-ratings-table' in attrs.get('class','').split():self.depth=1
        if self.depth==1 and tag=='tr':self.row=[]
        if self.depth==1 and tag=='td':self.parts=[]
    def handle_data(self,data):
        if self.parts is not None:self.parts.append(data)
    def handle_endtag(self,tag):
        if tag=='td' and self.parts is not None:
            self.row.append(' '.join(' '.join(self.parts).split()));self.parts=None
        if self.depth==1 and tag=='tr' and self.row:self.rows.append(self.row);self.row=None
        if tag=='table' and self.depth:self.depth-=1


def main():
    p=argparse.ArgumentParser();p.add_argument('input',type=Path);p.add_argument('--profile',choices=['sgu','guap'],required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    profile=SGU if a.profile=='sgu' else GUAP;body=a.input.read_bytes();secret=secrets.token_bytes(32)
    binding=SourceBinding(profile.source_id,profile.group_id,profile.year,profile.url,profile.url.split('/')[2],VERSION,'archive',True)
    parsed=parse_table(FetchResult(profile.url,body,'text/html',hashlib.sha256(body).hexdigest(),datetime.now(timezone.utc),'utf-8'),binding,secret,profile)
    if a.profile=='sgu':
        from audit_sgu import Reference
        reference=Reference();reference.feed(body.decode());rows=reference.rows
        expected=[(int(x['№']),Decimal(x['Сумма баллов'].replace(',','.')),{'Да':True,'Нет':False}.get(x['Согласие на зачисление']),int(x['Приоритет / ОВП / ВПП'].split('/')[0].strip()),'enrolled' if x['Статус зачисления']=='Зачислен' else 'unknown',scoped_candidate_key(binding,x['Код поступающего'],secret)) for x in rows]
    else:
        reference=Rows();reference.feed(body.decode());rows=reference.rows;expected=[]
        for row in rows:
            match=re.fullmatch(r'([A-Za-z0-9-]{1,64})(?:\s*\((Зачислен)\))?',row[1])
            if len(row)!=14 or match is None:raise RuntimeError('Reference schema differs;identifiers withheld')
            expected.append((int(row[0]),Decimal(row[3]),None,int(row[2]),'enrolled' if match[2] else 'unknown',scoped_candidate_key(binding,match[1],secret)))
    actual=[(x.official_rank,x.score,x.consent,x.priority,x.participation,x.candidate_key) for x in parsed.entries]
    if expected!=actual:raise RuntimeError('Independent facts differ;no rows/identifiers emitted')
    report={'recordedAt':datetime.now(timezone.utc).isoformat(),'success':True,'sourceUrl':profile.url,'adapterVersion':VERSION,'year':profile.year,'kind':'archive','checkedRows':len(rows),'places':parsed.seats,'consentUnknown':sum(x.consent is None for x in parsed.entries),'consentYes':sum(x.consent is True for x in parsed.entries),'enrolled':sum(x.participation=='enrolled' for x in parsed.entries),'ties':sum(v>1 for v in Counter(x.score for x in parsed.entries).values()),'boundaryChecked':[profile.seats,profile.seats+1] if profile.seats else [0,1],'originalSha256':hashlib.sha256(body).hexdigest(),'sourceUpdatedAt':None,'identifiersEmitted':False,'method':'Independent stdlib HTMLParser vs one config-driven BeautifulSoup decoder;all original rows'}
    a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))


if __name__=='__main__':main()
