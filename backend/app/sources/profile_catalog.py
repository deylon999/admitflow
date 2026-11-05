"""Bounded, content-addressed profile shards with an atomic manifest pointer.

Hashes detect artifact corruption; trusted code review still grants attestation.
"""
import hashlib
import json
import os
from pathlib import Path,PurePosixPath
import re
import tempfile

MAX_MANIFEST_BYTES=256*1024
MAX_SHARD_BYTES=1024*1024
MAX_TOTAL_BYTES=64*1024*1024
MAX_SHARDS=512
MAX_PROFILES=20_000
SHARD_PROFILES=100


def _pairs(items):
    result={}
    for key,value in items:
        if key in result:raise ValueError('duplicate JSON key')
        result[key]=value
    return result


def _read(path,limit):
    if path.is_symlink():raise ValueError('profile symlink')
    with path.open('rb') as stream:body=stream.read(limit+1)
    if not body or len(body)>limit:raise ValueError('profile artifact size')
    return body,json.loads(body,object_pairs_hook=_pairs)


def _document(data,limit):
    if (not isinstance(data,dict) or set(data)!={'format','profiles'} or data['format']!='reviewed-table-profiles-v1'
        or not isinstance(data['profiles'],dict) or not 1<=len(data['profiles'])<=limit):
        raise ValueError('profile document format')
    return data['profiles']


def active_catalog(root):
    root=Path(root)
    candidate=root/'catalog.json'
    return candidate if candidate.exists() or candidate.is_symlink() else root/'reviewed.json'


def read_profile_data(path):
    path=Path(path)
    body,data=_read(path,MAX_MANIFEST_BYTES)
    if not isinstance(data,dict):raise ValueError('profile manifest format')
    if data.get('format')=='reviewed-table-profiles-v1':
        if len(body)>128*1024:raise ValueError('legacy profile size')
        _document(data,100)
        return data
    if set(data)!={'format','profileCount','shards'} or data['format']!='reviewed-profile-catalog-v1':
        raise ValueError('profile manifest format')
    shards=data['shards'];count=data['profileCount']
    if type(count) is not int or not 1<=count<=MAX_PROFILES or not isinstance(shards,list) or not 1<=len(shards)<=MAX_SHARDS:
        raise ValueError('profile manifest limits')
    base=path.parent.resolve();profiles={};seen=set();size=len(body)
    for shard in shards:
        if (not isinstance(shard,dict) or set(shard)!={'file','sha256','count'} or type(shard['count']) is not int
            or not 1<=shard['count']<=SHARD_PROFILES or not isinstance(shard['sha256'],str)
            or not re.fullmatch(r'[a-f0-9]{64}',shard['sha256'])):raise ValueError('profile shard entry')
        name=shard['file']
        if not isinstance(name,str) or len(name)>160 or not re.fullmatch(r'[A-Za-z0-9_./-]+\.json',name):raise ValueError('profile shard path')
        relative=PurePosixPath(name)
        if relative.is_absolute() or '..' in relative.parts or name in seen:raise ValueError('duplicate or escaping shard')
        seen.add(name);candidate=base
        for part in relative.parts:
            candidate=candidate/part
            if candidate.is_symlink():raise ValueError('profile symlink')
        if not candidate.resolve().is_relative_to(base):raise ValueError('escaping shard')
        raw,document=_read(candidate,MAX_SHARD_BYTES);size+=len(raw)
        if size>MAX_TOTAL_BYTES or hashlib.sha256(raw).hexdigest()!=shard['sha256']:raise ValueError('profile shard hash/size')
        values=_document(document,SHARD_PROFILES)
        if len(values)!=shard['count'] or profiles.keys()&values.keys():raise ValueError('duplicate profile/count mismatch')
        profiles.update(values)
        if len(profiles)>MAX_PROFILES:raise ValueError('profile count limit')
    if len(profiles)!=count:raise ValueError('manifest count mismatch')
    return dict(format='reviewed-table-profiles-v1',profiles=profiles)


def _atomic_write(path,body):
    temporary=None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent,prefix=path.name+'.',suffix='.tmp',delete=False) as stream:
            temporary=Path(stream.name);stream.write(body)
        os.replace(temporary,path)
    finally:
        if temporary is not None:temporary.unlink(missing_ok=True)


def publish_profile_data(profiles,root):
    """Validate all scopes before publishing; retain all old shard artifacts."""
    from .table_profiles import build_profiles
    if not 1<=len(profiles)<=MAX_PROFILES:raise ValueError('profile count limit')
    build_profiles(dict(format='reviewed-table-profiles-v1',profiles=profiles))
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    if (root/'catalog.json').exists():
        old=read_profile_data(root/'catalog.json')['profiles']
        if not old.keys()<=profiles.keys() or any(profiles[name]!=fields for name,fields in old.items()):
            raise ValueError('existing reviewed profiles are immutable')
    directory=root/'shards'
    if directory.is_symlink():raise ValueError('profile shard symlink')
    directory.mkdir(exist_ok=True)
    groups={}
    for name,fields in sorted(profiles.items()):groups.setdefault(fields.get('version','reviewed-html-table-v1'),{})[name]=fields
    shards=[];size=0
    for _,values in sorted(groups.items()):
        items=list(values.items())
        for start in range(0,len(items),SHARD_PROFILES):
            chunk=dict(items[start:start+SHARD_PROFILES])
            raw=(json.dumps(dict(format='reviewed-table-profiles-v1',profiles=chunk),ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
            size+=len(raw)
            if len(raw)>MAX_SHARD_BYTES or size>MAX_TOTAL_BYTES:raise ValueError('profile artifact size')
            digest=hashlib.sha256(raw).hexdigest();name='shards/'+digest+'.json';path=root/name
            if path.exists():
                if path.is_symlink() or path.read_bytes()!=raw:raise ValueError('existing shard corruption')
            else:_atomic_write(path,raw)
            shards.append(dict(file=name,sha256=digest,count=len(chunk)))
    manifest=dict(format='reviewed-profile-catalog-v1',profileCount=len(profiles),shards=shards)
    raw=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode()
    if len(shards)>MAX_SHARDS or len(raw)>MAX_MANIFEST_BYTES:raise ValueError('profile manifest size')
    # Immutable shards may be orphaned after failure; the active manifest stays
    # unchanged until validation and all writes have succeeded.
    _atomic_write(root/'catalog.json',raw)
    return manifest
