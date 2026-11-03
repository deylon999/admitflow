#!/usr/bin/env python3
"""Compare all private original SGU rows via an independent stdlib parser; emit aggregates only."""
import argparse
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import secrets
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.sources.adapters.sgu2026 import GROUP_ID,SOURCE_ID,URL,VERSION,make_adapter
from app.sources.contracts import SourceBinding,scoped_candidate_key
from app.sources.fetcher import FetchResult


class Reference(HTMLParser):
    def __init__(self):
        super().__init__();self.rows=[];self.fields={};self.label=None;self.text=[]
    def handle_starttag(self,tag,attrs):
        if tag=='tr':self.fields={}
        if tag=='td':self.label=dict(attrs).get('data-label');self.text=[]
    def handle_data(self,data):
        if self.label:self.text.append(data)
    def handle_endtag(self,tag):
        if tag=='td' and self.label:
            self.fields[self.label]=' '.join(''.join(self.text).split());self.label=None
        if tag=='tr' and 'Код поступающего' in self.fields:
            self.rows.append(self.fields);self.fields={}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('input',type=Path);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    with args.input.open('rb') as file:body=file.read(8*1024*1024+1)
    secret=secrets.token_bytes(32)
    binding=SourceBinding(SOURCE_ID,GROUP_ID,2026,URL,'www.sgu.ru',VERSION,'archive',True)
    adapter=make_adapter(secret)
    result=adapter.parse(FetchResult(URL,body,'text/html',hashlib.sha256(body).hexdigest(),datetime.now(timezone.utc),'utf-8'),binding)
    reference=Reference();reference.feed(body.decode('utf-8'))
    if len(reference.rows)!=len(result.entries):raise RuntimeError('Original row count differs')
    for source,row in zip(reference.rows,result.entries):
        expected=(int(source['№']),Decimal(source['Сумма баллов'].replace(',','.')),
                  {'Да':True,'Нет':False}.get(source['Согласие на зачисление']),
                  int(source['Приоритет / ОВП / ВПП'].split('/')[0].strip()),
                  'enrolled' if source['Статус зачисления']=='Зачислен' else 'unknown',
                  scoped_candidate_key(binding,source['Код поступающего'],secret))
        actual=(row.official_rank,row.score,row.consent,row.priority,row.participation,row.candidate_key)
        if actual!=expected:raise RuntimeError('Original row facts differ; identifiers withheld')
    report=dict(verifiedAt=datetime.now(timezone.utc).isoformat(),success=True,sourceUrl=URL,adapterVersion=VERSION,kind='archive',year=2026,
                originalSha256=hashlib.sha256(body).hexdigest(),fixtureSha256=adapter.attestation.fixture_sha256,
                checkedRows=len(result.entries),boundaryRanksChecked=[16,17],generalSeats=result.seats,
                consentYes=sum(r.consent is True for r in result.entries),consentNo=sum(r.consent is False for r in result.entries),
                enrolled=sum(r.participation=='enrolled' for r in result.entries),
                tiedScoreGroups=sum(count>1 for count in Counter(r.score for r in result.entries).values()),
                sourceUpdatedAt=None,identifiersOrKeysEmitted=False,method='Independent stdlib HTMLParser vs BeautifulSoup adapter;all rows,including boundary/ties')
    args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))


if __name__=='__main__':main()
