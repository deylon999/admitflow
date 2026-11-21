#!/usr/bin/env python3
"""Derive GUAP fixture from original DOM; emit no original identifiers."""
import argparse,copy,hashlib,json,re
from pathlib import Path
from bs4 import BeautifulSoup


def sanitize(body):
    if not body or len(body)>8*1024*1024:raise ValueError('invalid_source_size')
    source=BeautifulSoup(body.decode('utf-8'),'html.parser');table=source.select('table.pk-ratings-table')
    if len(table)!=1:raise ValueError('invalid_table_count')
    original_rows=[r for r in table[0].select('tr') if r.find_all('td',recursive=False)]
    codes=[]
    for row in original_rows:
        cells=row.find_all('td',recursive=False)
        if len(cells)!=14:raise ValueError('invalid_columns')
        match=re.fullmatch(r'([A-Za-z0-9-]{1,64})(\s*\(Зачислен\))?',cells[1].get_text(' ',strip=True))
        if not match:raise ValueError('invalid_identifier_format')
        codes.append(match[1])
    if len(set(codes))!=len(codes):raise ValueError('duplicate_identifier')
    result=BeautifulSoup('', 'html.parser');outer,head,body_tag=(copy.copy(x) for x in [source.html,source.head,source.body])
    for node in (outer,head,body_tag):node.clear()
    if source.title:head.append(copy.deepcopy(source.title))
    outer.append(head);outer.append(body_tag);result.append(outer)
    for h in source.select('h1,h3')[:5]:body_tag.append(copy.deepcopy(h))
    cloned=copy.deepcopy(table[0]);body_tag.append(cloned)
    for index,row in enumerate([r for r in cloned.select('tr') if r.find_all('td',recursive=False)],1):
        cell=row.find_all('td',recursive=False)[1];enrolled='(Зачислен)' in cell.get_text();cell.clear();cell.append(f'FIXTURE-{index:06d}'+(' (Зачислен)' if enrolled else ''))
    for tag in result.find_all(True):tag.attrs={k:v for k,v in tag.attrs.items() if k in ('class','colspan','rowspan')}
    output=('<!-- DERIVED ANONYMIZED GUAP DOM;NOT ORIGINAL;archive2026 -->\n'+str(result)).encode()
    if any(code.encode() in output for code in codes):raise ValueError('original_identifier_survived')
    def facts(rows):return [[td.get_text(' ',strip=True) for j,td in enumerate(row.find_all('td',recursive=False)) if j!=1] for row in rows]
    if facts(original_rows)!=facts([r for r in cloned.select('tr') if r.find_all('td',recursive=False)]):raise ValueError('non_identifier_facts_changed')
    return output,len(codes)


def main():
    p=argparse.ArgumentParser();p.add_argument('input',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();body=a.input.read_bytes();output,rows=sanitize(body);a.output.mkdir(parents=True,exist_ok=False);(a.output/'derived.html').write_bytes(output)
    manifest={'format':'derived-guap-dom-v1','sourceUrl':'https://priem.guap.ru/bach/rating/list_1_1_1_3_1_f','originalSha256':hashlib.sha256(body).hexdigest(),'originalBytes':len(body),'fixtureSha256':hashlib.sha256(output).hexdigest(),'fixtureBytes':len(output),'rows':rows,'season':2026,'kind':'archive','transformations':['actual html/head/body/title,heading/table DOM subset','public codes replaced;enrollment suffix preserved','all non-structural attributes removed;all other row cells unchanged'],'attested':False}
    (a.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({'rows':rows,'fixtureBytes':len(output),'fixtureSha256':manifest['fixtureSha256']}))


if __name__=='__main__':main()
