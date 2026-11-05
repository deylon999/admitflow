"""Independent stdlib audit of every original row before immutable publication.

Raw composite identifiers stay private. Only counts, hashes and public scope
metadata are written; no candidate key, code, score or hidden-state value exits.
"""
import argparse,copy,hashlib,hmac,json,re,secrets,sys
from datetime import datetime
from decimal import Decimal
from html.parser import HTMLParser
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.sources.contracts import SourceBinding
from app.sources.fetcher import FetchResult
from app.sources.profile_catalog import active_catalog,read_profile_data,publish_profile_data
from app.sources.table_family import parse_table
from app.sources.table_profiles import build_profiles


def clean(parts):return ' '.join(' '.join(parts).split())


class IndependentRows(HTMLParser):
    def __init__(self):
        super().__init__();self.depth=0;self.target=None;self.rows=[];self.row=[];self.cell=None;self.spans=[]
        self.metadata={};self.meta=None;self.div_depth=0
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='div':
            self.div_depth+=1
            if attrs.get('id') in ('MainContent_divPlanPriem','MainContent_divCountPeaple'):
                if self.meta:raise ValueError('nested source metadata')
                self.meta=(attrs['id'],self.div_depth,[])
        if tag=='table':
            self.depth+=1
            if attrs.get('id')=='rating':
                if self.target is not None:raise ValueError('duplicate candidate table')
                self.target=self.depth
        if self.target!=self.depth:return
        if tag=='tr':self.row=[]
        if tag=='td':self.cell=dict(parts=[],spans=[],classes=attrs.get('class',''));self.spans=[]
        if tag=='span' and self.cell is not None:self.spans.append(dict(classes=attrs.get('class','').split(),parts=[]))
    def handle_data(self,data):
        if self.meta:self.meta[2].append(data)
        if self.cell is not None and self.target==self.depth:
            self.cell['parts'].append(data)
            for span in self.spans:span['parts'].append(data)
    def handle_endtag(self,tag):
        if tag=='div':
            if self.meta and self.meta[1]==self.div_depth:
                ident,_,parts=self.meta
                if ident in self.metadata:raise ValueError('duplicate source metadata')
                self.metadata[ident]=clean(parts);self.meta=None
            self.div_depth-=1
        if self.target==self.depth:
            if tag=='span' and self.cell is not None and self.spans:self.cell['spans'].append(self.spans.pop())
            if tag=='td' and self.cell is not None:
                self.cell['text']=clean(self.cell.pop('parts'));self.row.append(self.cell);self.cell=None
            if tag=='tr' and self.row:self.rows.append(self.row);self.row=[]
        if tag=='table':
            if self.target==self.depth:self.target=None
            self.depth-=1


def compare_rows(body,profile,parsed,secret):
    reader=IndependentRows();reader.feed(body.decode('utf-8'));seen=set();enrolled_count=0
    if len(reader.rows)!=profile.rows or len(parsed.entries)!=profile.rows:raise ValueError('independent row count mismatch')
    if reader.metadata.get('MainContent_divPlanPriem')!='План приема (количество мест) - '+str(profile.seats):raise ValueError('independent capacity mismatch')
    if not re.match(r'^Количество заявлений - '+str(profile.rows)+r' \(',reader.metadata.get('MainContent_divCountPeaple','')):raise ValueError('independent source count mismatch')
    for ordinal,(cells,actual) in enumerate(zip(reader.rows,parsed.entries,strict=True),1):
        if len(cells)!=17 or cells[0]['text']!=str(ordinal) or cells[4]['text']!=str(ordinal):raise ValueError('independent official order mismatch')
        ids=[span for span in cells[3]['spans'] if 'text-secondary' in span['classes']]
        if len(ids)!=1:raise ValueError('independent code node mismatch')
        pieces=clean(ids[0]['parts']).split('/')
        if len(pieces)!=3 or [len(x) for x in pieces[:2]]!=[5,11] or len(pieces[2]) not in (6,7) or not all(x.isascii() and x.isdigit() for x in pieces):raise ValueError('independent code format mismatch')
        identifier=pieces[0]
        if identifier in seen:raise ValueError('independent minimal identity duplicate')
        seen.add(identifier)
        expected_key=hmac.new(secret,json.dumps([profile.source_id,profile.group_id,profile.year,identifier],ensure_ascii=False,separators=(',',':')).encode(),hashlib.sha256).hexdigest()
        status=[span for span in cells[3]['spans'] if 'text-success' in span['classes']]
        if len(status)>1 or any(not re.fullmatch(r'Зачислен \(Приказ №\s+[^\s()]+\s+от\s+\d{2}\.\d{2}\.2026\)',clean(s['parts'])) for s in status):raise ValueError('independent enrollment mismatch')
        enrolled=bool(status);enrolled_count+=enrolled
        if cells[15]['text']!='Организация строительного производства':raise ValueError('independent program mismatch')
        expected=(ordinal,expected_key,Decimal(cells[6]['text'].replace(',','.')),None,None,'enrolled' if enrolled else 'unknown')
        observed=(actual.official_rank,actual.candidate_key,actual.score,actual.consent,actual.priority,actual.participation)
        if observed!=expected:raise ValueError('independent candidate facts mismatch')
    return dict(checkedRows=len(reader.rows),uniqueMinimalIds=len(seen),explicitEnrolled=enrolled_count,seats=profile.seats,
        fields=['official_order','minimal_scoped_identity','total_score','unknown_consent','unknown_priority','explicit_enrollment_or_unknown','public_program'],allFieldsMatched=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--publish',action='store_true');args=parser.parse_args()
    scope=json.loads((ROOT/'docs/sources/bgu2026-scope.json').read_text(encoding='utf-8'));fields=copy.deepcopy(scope['profile'])
    body=(ROOT/'backend/var/research/b17-bgu'/(scope['originalSha256']+'.body')).read_bytes()
    if hashlib.sha256(body).hexdigest()!=scope['originalSha256']:raise ValueError('private original integrity mismatch')
    fixture_path='backend/tests/fixtures/filtered-table/bgu2026-construction.html';fixture=(ROOT/fixture_path).read_bytes()
    fields['proof']=dict(passport='docs/sources/bgu2026.md',fixture=fixture_path,fixture_sha256=hashlib.sha256(fixture).hexdigest(),
        original_sha256=scope['originalSha256'],source_url=fields['url'],year=2026,kind='archive',sample_rows=109,checked_rows=109,
        verified_at=scope['checkedAt'],adapter_version=fields['version'])
    profile=build_profiles(dict(format='reviewed-table-profiles-v1',profiles={fields['source_id']:fields}))[fields['source_id']]
    binding=SourceBinding(profile.source_id,profile.group_id,2026,profile.url,'bgu.ru',profile.version,'archive',True)
    secret=secrets.token_bytes(32);raw=FetchResult(profile.url,body,'text/html',scope['originalSha256'],datetime.fromisoformat(scope['checkedAt']),'utf-8')
    parsed=parse_table(raw,binding,secret,profile);audit=compare_rows(body,profile,parsed,secret)
    synthetic=FetchResult(profile.url,fixture,'text/html',profile.proof.fixture_sha256,raw.fetched_at,'utf-8')
    compare_rows(fixture,profile,parse_table(synthetic,binding,secret,profile),secret)
    if args.publish:
        root=ROOT/'backend/app/sources/profiles';data=read_profile_data(active_catalog(root))['profiles']
        if profile.source_id in data and data[profile.source_id]!=fields:raise ValueError('existing reviewed profile immutable')
        if not (ROOT/profile.proof.passport).is_file():raise ValueError('passport required before publication')
        publish_profile_data({**data,profile.source_id:fields},root)
    result=dict(sourceId=profile.source_id,url=profile.url,originalSha256=scope['originalSha256'],fixtureSha256=profile.proof.fixture_sha256,
        reviewedAt=scope['checkedAt'],version=profile.version,independentParser='stdlib.HTMLParser',**audit,kind='archive',
        minimalIdRule='first5digits before first slash; other parts discarded',realCandidateValuesInTrackedFixture=False,
        candidateKeysExported=False,sourceTimestamp='unknown_timezone',publishedToManifest=args.publish,sourceEnabled=False)
    (ROOT/'docs/evidence/b17-bgu-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result))


if __name__=='__main__':main()
