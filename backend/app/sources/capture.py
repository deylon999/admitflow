"""Capture original pilot responses for offline review; never enable an adapter."""
import argparse
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, ValidationError

from ..worker import bounded_fetch
from .contracts import SourceBinding
from .fetcher import FetchError

TARGETS = {
    'sgu-2026-4588': 'https://www.sgu.ru/svodka/4588',
    'sgups-2026-1348': 'https://www.stu.ru/abiturient/abiturients_table.php?bez_ispitanii=-1&celev=-1&fin=%D0%91%D0%AE%D0%94&flag=ks&forma_obucheniya=1&lgoti=-1&specializ=1348&type=konkursnie_spiski_obshii_bud&uroven_podgotovki=1',
}
MAX_BYTES = 5*1024*1024


class CaptureError(Exception):
    pass


class Manifest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    format: str = Field(pattern='^pilot-capture-v1$')
    source_key: str
    source_url: str
    final_url: str = Field(max_length=4096)
    season: int = Field(ge=2026, le=2026)
    data_kind: str = Field(pattern='^archive$')
    attested: bool
    fetched_at: AwareDatetime
    content_type: str = Field(max_length=100)
    charset: str | None = Field(max_length=100)
    payload_hash: str = Field(pattern='^[a-f0-9]{64}$')
    payload_bytes: int = Field(gt=0, le=MAX_BYTES)


def verify(folder):
    folder = Path(folder)
    manifest_path, payload_path = folder/'manifest.json', folder/'response.bin'
    if manifest_path.is_symlink() or payload_path.is_symlink():
        raise CaptureError('unsafe_capture_path')
    try:
        with manifest_path.open('rb') as file:
            body = file.read(16385)
        if len(body) > 16384:
            raise CaptureError('invalid_capture_manifest')
        manifest = Manifest.model_validate_json(body)
        target = TARGETS.get(manifest.source_key)
        final = urlsplit(manifest.final_url)
        if not target or manifest.source_url != target or manifest.attested or final.scheme != 'https' or final.hostname != urlsplit(target).hostname or final.port not in (None,443) or final.username or final.password or final.fragment:
            raise CaptureError('invalid_capture_binding')
        with payload_path.open('rb') as file:
            payload = file.read(MAX_BYTES+1)
        if len(payload) != manifest.payload_bytes or hashlib.sha256(payload).hexdigest() != manifest.payload_hash:
            raise CaptureError('capture_hash_mismatch')
        return manifest
    except (OSError,ValueError,ValidationError):
        raise CaptureError('invalid_capture_bundle') from None


def capture(source_key, output, *, fetch=bounded_fetch):
    if source_key not in TARGETS:
        raise CaptureError('unknown_capture_target')
    url = TARGETS[source_key]
    domain = urlsplit(url).hostname
    binding = SourceBinding('capture',source_key,2026,url,domain,'capture-only','archive',False)
    result = fetch(binding,frozenset({domain}))
    if not result.body or len(result.body)>MAX_BYTES or hashlib.sha256(result.body).hexdigest()!=result.payload_hash:
        raise CaptureError('invalid_capture_payload')
    manifest = Manifest(format='pilot-capture-v1',source_key=source_key,source_url=url,final_url=result.url,season=2026,data_kind='archive',attested=False,fetched_at=result.fetched_at,content_type=result.content_type,charset=result.charset,payload_hash=result.payload_hash,payload_bytes=len(result.body))
    root = Path(output).resolve()
    root.mkdir(parents=True,exist_ok=True,mode=0o700)
    folder = root/f'capture-{uuid4()}'
    temporary = root/f'.writing-{uuid4()}'
    temporary.mkdir(mode=0o700)
    try:
        for name, body in [('response.bin',result.body),('manifest.json',manifest.model_dump_json(indent=2).encode())]:
            with os.fdopen(os.open(temporary/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as file:
                file.write(body)
                file.flush()
                os.fsync(file.fileno())
        verify(temporary)
        temporary.rename(folder)
        return folder
    finally:
        if temporary.exists():
            for name in ('response.bin','manifest.json'):
                (temporary/name).unlink(missing_ok=True)
            temporary.rmdir()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command',required=True)
    get = sub.add_parser('fetch')
    get.add_argument('target',choices=TARGETS)
    get.add_argument('--output',default='./var/captures')
    check = sub.add_parser('verify')
    check.add_argument('folder')
    args = parser.parse_args(argv)
    try:
        if args.command == 'fetch':
            print(json.dumps({'folder':str(capture(args.target,args.output)),'attested':False}))
        else:
            result = verify(args.folder)
            print(json.dumps({'sourceKey':result.source_key,'payloadHash':result.payload_hash,'bytes':result.payload_bytes,'attested':False}))
        return 0
    except FetchError as error:
        print(json.dumps({'error':error.code,'captured':False}))
    except CaptureError as error:
        print(json.dumps({'error':str(error),'captured':False}))
    except Exception:
        print(json.dumps({'error':'capture_failed','captured':False}))
    return 1


if __name__=='__main__':
    raise SystemExit(main())
