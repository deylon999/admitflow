"""Separate worker process. Production cannot execute unattested adapters."""
import argparse
import hashlib
import json
import logging
import math
import multiprocessing
import os
from pathlib import Path
import tempfile
import time
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy.orm import Session

from .admissions import Source
from .config import Settings
from .database import make_engine
from .jobs import LostLease, claim, clock, complete, fail, guard_lease, renew
from .sources.contracts import AdapterError
from .sources.fetcher import FetchError, Fetcher, FetchPolicy, FetchResult
from .sources.publishing import FETCH_CODES, binding_from_db, publish
from .sources.registry import PRODUCTION_REGISTRY, runtime_registry
from .sources.storage import RawStore, StorageError
from .sources.validation import Quarantined


class FetchMetadata(BaseModel):
    model_config=ConfigDict(extra='forbid')
    state: Literal['ok']
    url: str = Field(max_length=4096)
    content_type: Literal['text/html','application/json','text/csv','text/plain']
    payload_hash: str = Field(pattern='^[a-f0-9]{64}$')
    fetched_at: AwareDatetime
    charset: str | None = Field(max_length=100)
    byte_count: int = Field(strict=True,ge=1,le=8*1024*1024)


def _private_write(path,body):
    with os.fdopen(os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as file:
        file.write(body)


def _fetch_child(folder,binding,domains,max_bytes=5*1024*1024):
    folder=Path(folder)
    try:
        result=Fetcher(FetchPolicy(domains=domains,max_bytes=max_bytes)).fetch(binding.url)
        metadata=FetchMetadata(state='ok',url=result.url,content_type=result.content_type,payload_hash=result.payload_hash,fetched_at=result.fetched_at,charset=result.charset,byte_count=len(result.body))
        _private_write(folder/'payload.bin',result.body)
        message=metadata.model_dump(mode='json')
    except FetchError as error:
        message=dict(state='error',code=error.code,retryAfter=error.retry_after)
    except Exception:
        message=dict(state='error',code='network_error',retryAfter=60)
    try:
        _private_write(folder/'result.writing',json.dumps(message).encode())
        (folder/'result.writing').rename(folder/'result.json')
    except Exception:
        # Parent sees a missing/incomplete envelope, never exception text or raw.
        return


def _read_fetch_result(folder,max_bytes=5*1024*1024):
    try:
        with (folder/'result.json').open('rb') as file:
            payload=file.read(16385)
        if len(payload)>16384:
            raise ValueError()
        message=json.loads(payload)
        if not isinstance(message,dict):
            raise ValueError()
        if message.get('state')=='error':
            if set(message)!={'state','code','retryAfter'} or message['code'] not in FETCH_CODES:
                raise ValueError()
            delay=message['retryAfter']
            if delay is not None and (type(delay) is not int or not 30<=delay<=86400):
                raise ValueError()
            raise FetchError(message['code'],retry_after=delay)
        metadata=FetchMetadata.model_validate(message)
        if metadata.byte_count > max_bytes:
            raise ValueError()
        with (folder/'payload.bin').open('rb') as file:
            body=file.read(max_bytes+1)
        if len(body)!=metadata.byte_count or hashlib.sha256(body).hexdigest()!=metadata.payload_hash:
            raise ValueError()
        return FetchResult(metadata.url,body,metadata.content_type,metadata.payload_hash,metadata.fetched_at,metadata.charset)
    except FetchError:
        raise
    except (OSError,ValueError,TypeError,ValidationError):
        raise FetchError('invalid_headers') from None


def cleanup_fetch_folder(folder):
    incomplete = False
    for name in ('payload.bin','result.writing','result.json'):
        try:
            (folder/name).unlink(missing_ok=True)
        except OSError:
            incomplete = True
    try:
        folder.rmdir()
    except OSError:
        incomplete = True
    if incomplete:
        logging.getLogger('admitflow.worker').warning('fetch_cleanup_incomplete')


def bounded_fetch(binding,domains,*,timeout=50,max_bytes=5*1024*1024):
    # Wait for process exit, not a pipe prefix followed by an unbounded recv.
    if not isinstance(timeout,(int,float)) or not math.isfinite(timeout) or timeout<=0:
        raise ValueError('invalid_fetch_timeout')
    FetchPolicy(domains=domains,max_bytes=max_bytes)  # Validate before spawning a process.
    deadline=time.monotonic()+timeout
    ctx=multiprocessing.get_context('spawn')
    folder=Path(tempfile.mkdtemp(prefix='admitflow-fetch-')).resolve()
    process=ctx.Process(target=_fetch_child,args=(str(folder),binding,domains,max_bytes),daemon=True)
    try:
        process.start()
        process.join(max(0,deadline-time.monotonic()))
        if process.is_alive():
            raise FetchError('timeout',retry_after=60)
        if process.exitcode!=0:
            raise FetchError('network_error',retry_after=60)
        return _read_fetch_result(folder,max_bytes=max_bytes)
    finally:
        try:
            if process.pid is not None:
                if process.is_alive():
                    process.terminate()
                process.join(2)
                if process.is_alive():
                    process.kill()
                    process.join(2)
                if not process.is_alive():
                    process.close()
                else:
                    logging.getLogger('admitflow.worker').warning('fetch_process_cleanup_incomplete')
        except (OSError, ValueError):
            logging.getLogger('admitflow.worker').warning('fetch_process_cleanup_incomplete')
        finally:
            # Only known files in the directory we created; no recursive deletion.
            cleanup_fetch_folder(folder)


def run_once(engine,store,*,registry=PRODUCTION_REGISTRY,fetch=bounded_fetch,now=clock,allow_unattested=False):
    lease=claim(engine,now=now())
    if lease is None:
        return {'state':'idle'}
    try:
        with Session(engine) as db:
            source=db.get(Source,lease.source_id)
            binding=binding_from_db(db,source)
            adapter=registry.resolve(binding,allow_unattested=allow_unattested)
        raw=fetch(binding,adapter.domains,**({'max_bytes':adapter.max_bytes} if adapter.max_bytes != 5*1024*1024 else {}))
        renew(engine,lease,now=now())
        store.put(raw.body,raw.payload_hash)
        parsed=adapter.parse(raw,binding)
        renew(engine,lease,now=now())
        publish(engine,lease.source_id,parsed,raw,store,registry=registry,allow_unattested=allow_unattested,expected_binding=binding,lease_guard=lambda db:guard_lease(db,lease,now=now()))
        complete(engine,lease,now=now())
        return {'state':'success','sourceId':lease.source_id}
    except LostLease:
        return {'state':'lost_lease','sourceId':lease.source_id}
    except Exception as error:
        if isinstance(error,FetchError):
            code,retry_after=error.code,error.retry_after
        elif isinstance(error,StorageError):
            code=error.code
            retry_after=60 if code in ('raw_lock_timeout','raw_write_failed') else None
        elif isinstance(error,(Quarantined,AdapterError)):
            code,retry_after=error.code,None
        elif isinstance(error,ValidationError):
            code,retry_after='invalid_schema',None
        else:
            code,retry_after='internal_error',60
        try:
            fail(engine,lease,code,retry_after=retry_after,now=now())
        except LostLease:
            return {'state':'lost_lease','sourceId':lease.source_id}
        # Do not log exception strings, URLs, raw bodies or public IDs.
        return {'state':'failed','sourceId':lease.source_id}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['once','loop'])
    parser.add_argument('--poll-seconds',type=float,default=5)
    args=parser.parse_args(argv)
    if not 1<=args.poll_seconds<=60:
        parser.error('poll-seconds must be between 1 and 60')
    engine=make_engine(Settings.from_env().database_url)
    store=RawStore(os.getenv('RAW_STORE_PATH','./var/raw'))
    try:
        registry=runtime_registry()
        while True:
            try:
                result=run_once(engine,store,registry=registry)
            except Exception:
                result={'state':'worker_error'}
            print(json.dumps(result),flush=True)
            if args.mode=='once':
                return 1 if result['state'] in ('failed','worker_error') else 0
            # Polling is bounded even after persistent DB/adapter failures.
            time.sleep(args.poll_seconds)
    except KeyboardInterrupt:
        return 0
    finally:
        engine.dispose()


if __name__=='__main__':
    raise SystemExit(main())
