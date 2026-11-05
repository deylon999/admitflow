"""Validated, versioned reference catalog; no network or source registration.

The public organisation directory ships as a read-only artifact. Personal data,
subscriptions and the small operator-owned source registry remain in the DB.
"""
import argparse
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from types import MappingProxyType
from urllib.parse import urlsplit

DEFAULT_PATH = Path(__file__).with_name('data')/'national-catalog.json'
# Reviewed external identities; never deduplicate institutions merely by name/host.
LEGACY_IDS = MappingProxyType({'258':'sgu-saratov','1715':'sgups-novosibirsk','243':'guap-spb'})


@dataclass(frozen=True)
class Institution:
    registry_id: str
    name: str
    region: str
    region_id: str
    is_branch: bool
    provenance_url: str
    official_url: str | None
    parent_registry_id: str | None

    @property
    def id(self):
        return LEGACY_IDS.get(self.registry_id, 'miccedu-'+self.registry_id)


@dataclass(frozen=True)
class CatalogSnapshot:
    institutions: tuple[Institution, ...]
    edition: int
    captured_at: datetime
    sha256: str
    region_count: int
    source_url: str


def valid_url(value, *, provenance=False):
    if not isinstance(value,str) or len(value)>2048 or re.search(r'[\s\x00-\x1f\x7f\\]',value):
        raise ValueError('invalid catalog URL')
    try:
        parts=urlsplit(value)
        if parts.scheme not in ('http','https') or not parts.hostname or parts.username or parts.password:
            raise ValueError()
        parts.port
        if provenance and (parts.scheme!='https' or parts.hostname!='monitoring.miccedu.ru'):
            raise ValueError()
    except ValueError:
        raise ValueError('invalid catalog URL') from None
    return value


def clean_text(value, maximum):
    if not isinstance(value,str) or not value.strip() or len(value)>maximum or re.search(r'[\x00-\x1f\x7f]',value):
        raise ValueError('invalid catalog text')
    return value


def parse_snapshot(body):
    if not isinstance(body,bytes) or not 1<=len(body)<=5*1024*1024:
        raise ValueError('invalid catalog size')
    try:
        data=json.loads(body.decode('utf-8'))
        if data['format']!='miccedu-catalog-v1' or data['scope']!='monitoring-participants' or data['nationalTotal'] is not None:
            raise ValueError('unsupported catalog scope')
        edition=data['edition']
        if type(edition) is not int or not 2025<=edition<=2100: raise ValueError('invalid edition')
        captured=datetime.fromisoformat(data['capturedAt'])
        if captured.tzinfo is None: raise ValueError('timestamp requires timezone')
        records=[]
        for row in data['institutions']:
            ident=row['registryId'];parent=row['parentRegistryId']
            if not isinstance(ident,str) or not re.fullmatch(r'\d{1,12}',ident): raise ValueError('invalid identifier')
            if parent is not None and (not isinstance(parent,str) or not re.fullmatch(r'\d{1,12}',parent) or parent==ident):
                raise ValueError('invalid parent')
            if type(row['isBranch']) is not bool: raise ValueError('invalid branch flag')
            region_id=row['regionId']
            if not isinstance(region_id,str) or not re.fullmatch(r'\d{5}',region_id): raise ValueError('invalid region')
            url=valid_url(row['provenanceUrl'],provenance=True)
            if url != f'https://monitoring.miccedu.ru/iam/{edition}/_vpo/inst.php?id={ident}':
                raise ValueError('inconsistent provenance')
            records.append(Institution(ident,clean_text(row['name'],1500),clean_text(row['region'],120),region_id,row['isBranch'],url,
                                       valid_url(row['officialUrl']) if row['officialUrl'] is not None else None,parent))
        ids=[r.registry_id for r in records]
        if not records or len(ids)!=len(set(ids)) or data['recordCount']!=len(records) or data['headlineTotal']!=len(records):
            raise ValueError('duplicate or inconsistent catalog count')
        if data['branchCount']!=sum(r.is_branch for r in records): raise ValueError('inconsistent branch count')
        if not isinstance(data['regionCount'],int) or not 1<=data['regionCount']<=100: raise ValueError('invalid region count')
        if len({r.region_id for r in records})>data['regionCount']: raise ValueError('inconsistent regions')
        for capture in data['captures']:
            valid_url(capture['url'],provenance=True)
            if not re.fullmatch(r'[a-f0-9]{64}',capture['sha256']): raise ValueError('invalid capture hash')
            if datetime.fromisoformat(capture['fetchedAt']).tzinfo is None: raise ValueError('invalid capture timestamp')
        return CatalogSnapshot(tuple(records),edition,captured,hashlib.sha256(body).hexdigest(),data['regionCount'],valid_url(data['sourceUrl'],provenance=True))
    except (KeyError,TypeError,UnicodeError,json.JSONDecodeError) as error:
        raise ValueError('invalid catalog snapshot') from error


@lru_cache(maxsize=1)
def load_catalog():
    return parse_snapshot(DEFAULT_PATH.read_bytes())


def import_snapshot(source, target):
    """Validate the entire artifact before atomic replacement; no partial import."""
    body=Path(source).read_bytes()
    snapshot=parse_snapshot(body)
    target=Path(target)
    target.parent.mkdir(parents=True,exist_ok=True)
    temporary=None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent,prefix=target.name+'.',suffix='.tmp',delete=False) as out:
            temporary=Path(out.name)
            out.write(body)
        os.replace(temporary,target)
    finally:
        if temporary is not None: temporary.unlink(missing_ok=True)
    return snapshot


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['validate','import'])
    parser.add_argument('--input',type=Path,default=DEFAULT_PATH)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.action=='import':
        if args.output is None: parser.error('import requires --output')
        result=import_snapshot(args.input,args.output)
    else: result=parse_snapshot(args.input.read_bytes())
    print(json.dumps(dict(records=len(result.institutions),branches=sum(r.is_branch for r in result.institutions),
                         sites=sum(r.official_url is not None for r in result.institutions),edition=result.edition,
                         sha256=result.sha256,nationalTotal=None)))


if __name__=='__main__': main()
