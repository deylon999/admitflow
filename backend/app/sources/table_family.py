"""One bounded HTML-table decoder driven by reviewed source profiles."""
from dataclasses import dataclass
from decimal import Decimal,InvalidOperation
import hashlib
import re
from urllib.parse import urlsplit
from .contracts import AdapterError,CandidateRow,ParsedList,scoped_candidate_key
from .html_inspection import document
from .registry import Adapter,Attestation

VERSION='reviewed-html-table-v1'


def clean(value):return ' '.join(value.replace(r'\xa0',' ').split())


@dataclass(frozen=True)
class TableProfile:
    source_id:str
    group_id:str
    url:str
    year:int
    rows:int
    seats:int
    table_selector:str
    row_selector:str
    columns:tuple[tuple[str,int|str],...]
    cell_count:int
    headers:tuple[str,...]
    identity:tuple[tuple[str,str],...]
    proof:Attestation|None=None
    cell_labels:tuple[str,...]=()
    priority_pattern:str=r'([0-9]{1,4})'
    public_code_enrolled_suffix:bool=False
    kind:str='archive'
    season_pattern:str=r'Приемная кампания\s+([0-9]{4})'

    def __post_init__(self):
        from .fetcher import valid_domains
        url=urlsplit(self.url)
        valid=(url.scheme=='https' and not url.username and not url.password and not url.fragment and url.port in (None,443)
            and valid_domains(frozenset({url.hostname})) and self.kind in ('archive','live') and type(self.year) is int and 2000<=self.year<=2100
            and type(self.rows) is int and 1<=self.rows<=100_000 and type(self.seats) is int and 0<=self.seats<=1_000_000
            and type(self.cell_count) is int and 1<=self.cell_count<=100
            and isinstance(self.headers,tuple) and bool(self.headers) and isinstance(self.identity,tuple) and bool(self.identity)
            and len({name for name,_ in self.columns})==len(self.columns) and {'rank','code','score'}<={name for name,_ in self.columns}
            and all(name in ('rank','code','score','consent','priority','status') and ((type(column) is int and 0<=column<self.cell_count) or (isinstance(column,str) and column in self.cell_labels)) for name,column in self.columns))
        if not valid:raise ValueError('invalid_table_profile')
        re.compile(self.season_pattern);re.compile(self.priority_pattern)

    def binding_matches(self,binding):
        return (binding.source_id,binding.group_id,binding.url,binding.domain,binding.year,binding.kind,binding.adapter_version)==(
            self.source_id,self.group_id,self.url,urlsplit(self.url).hostname,self.year,self.kind,VERSION)


def parse_table(response,binding,secret,profile):
    if not profile.binding_matches(binding) or response.url!=profile.url:raise AdapterError('invalid_binding')
    if not binding.enabled:raise AdapterError('source_disabled')
    try:
        if response.content_type!='text/html' or (response.charset or 'utf-8').lower() not in ('utf-8','utf8') or hashlib.sha256(response.body).hexdigest()!=response.payload_hash or not response.body.rstrip().endswith(b'</html>'):raise ValueError()
        soup=document(response.body)
        if soup.select('.pagination,.pager,a[rel="next"]'):raise ValueError()
        seasons={int(match[1]) for text in soup.find_all(string=True) if (match:=re.search(profile.season_pattern,text.strip()))}
        if seasons!={profile.year}:raise ValueError()
        identity={}
        for selector,expected in profile.identity:identity.setdefault(selector,[]).append(expected)
        for selector,expected in identity.items():
            if sorted(clean(node.get_text(' ',strip=True)) for node in soup.select(selector))!=sorted(expected):raise ValueError()
        tables=soup.select(profile.table_selector)
        if len(tables)!=1:raise ValueError()
        table=tables[0];headers=tuple(clean(h.get_text(' ',strip=True)) for h in table.select('th'))
        if headers!=profile.headers:raise ValueError()
        rows=[row for row in table.select(profile.row_selector) if row.find_all('td',recursive=False)]
        if len(rows)!=profile.rows:raise ValueError()
        entries=[];seen=set()
        for index,row in enumerate(rows,1):
            cells=row.find_all('td',recursive=False)
            if len(cells)!=profile.cell_count:raise ValueError()
            labels=[td.get('data-label') for td in cells]
            if profile.cell_labels and tuple(labels)!=profile.cell_labels:raise ValueError()
            by_label={td.get('data-label'):td for td in cells}
            fields={name:clean((cells[column] if isinstance(column,int) else by_label[column]).get_text(' ',strip=True)) for name,column in profile.columns}
            if fields['rank']!=str(index):raise ValueError()
            code=fields['code'];enrolled=False
            if profile.public_code_enrolled_suffix:
                match=re.fullmatch(r'([A-Za-z0-9-]{1,64})(?:\s*\((Зачислен)\))?',code)
                if match is None:raise ValueError()
                code=match[1];enrolled=bool(match[2])
            if not re.fullmatch(r'[A-Za-z0-9-]{1,64}',code):raise ValueError()
            key=scoped_candidate_key(binding,code,secret)
            if key in seen:raise ValueError()
            seen.add(key)
            score_text=fields['score'];score=None
            if score_text not in ('','-','---'):
                if not re.fullmatch(r'[0-9]{1,4}(?:[.,][0-9]{1,2})?',score_text):raise ValueError()
                score=Decimal(score_text.replace(',','.'))
            consent=fields.get('consent')
            if consent not in (None,'Да','Нет','---',''):raise ValueError()
            priority_text=fields.get('priority');priority=None
            if priority_text not in (None,'','---','-'):
                match=re.fullmatch(profile.priority_pattern,priority_text)
                if match is None:raise ValueError()
                priority=int(match[1])
            status=fields.get('status')
            if status not in (None,'','---','Зачислен'):raise ValueError()
            enrolled=enrolled or status=='Зачислен'
            entries.append(CandidateRow(candidate_key=key,row_ref=f'row/{index}',official_rank=index,score=score,consent={'Да':True,'Нет':False}.get(consent),priority=priority,participation='enrolled' if enrolled else 'unknown'))
        warnings=['no_source_timestamp']
        if any(row.consent is None for row in entries):warnings.append('unknown_consent')
        if any(row.priority is None for row in entries):warnings.append('unknown_priority')
        return ParsedList(source_id=binding.source_id,group_id=binding.group_id,year=profile.year,adapter_version=VERSION,kind=profile.kind,complete=True,expected_rows=profile.rows,seats=profile.seats,source_updated_at=None,entries=tuple(entries),warnings=tuple(warnings))
    except AdapterError:raise
    except (ValueError,TypeError,KeyError,IndexError,InvalidOperation):raise AdapterError('invalid_format') from None


def make_table_adapter(secret,profiles):
    if not isinstance(secret,bytes) or len(secret)<32:raise ValueError('source_identity_key_required')
    profiles=tuple(profiles)
    if not profiles or len({p.url for p in profiles})!=len(profiles) or any(p.proof is None for p in profiles):raise ValueError('reviewed_profiles_required')
    by_url={profile.url:profile for profile in profiles}
    def decode(response,binding):
        profile=by_url.get(binding.url)
        if profile is None:raise AdapterError('invalid_binding')
        return parse_table(response,binding,secret,profile)
    return Adapter(VERSION,frozenset(urlsplit(p.url).hostname for p in profiles),decode,attested=True,attestations=tuple(p.proof for p in profiles),max_bytes=8*1024*1024)
