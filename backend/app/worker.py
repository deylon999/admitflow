"""Separate worker process. Production cannot execute unattested adapters."""
import argparse
import json
import multiprocessing
import os
import time

from pydantic import ValidationError
from sqlalchemy.orm import Session

from .admissions import Source
from .config import Settings
from .database import make_engine
from .jobs import LostLease, claim, clock, complete, fail, guard_lease
from .sources.contracts import AdapterError
from .sources.fetcher import FetchError, Fetcher, FetchPolicy
from .sources.publishing import binding_from_db, publish
from .sources.registry import PRODUCTION_REGISTRY
from .sources.storage import RawStore, StorageError
from .sources.validation import Quarantined


def _fetch_child(send,binding,domains):
    try:
        result=Fetcher(FetchPolicy(domains=domains)).fetch(binding.url)
        send.send(('ok',result))
    except FetchError as error:
        send.send(('error',error.code,error.retry_after))
    except Exception:
        send.send(('error','network_error',60))
    finally:
        send.close()


def bounded_fetch(binding,domains,*,timeout=50):
    # An OS resolver may ignore socket timeouts. Bound it in a disposable process.
    ctx=multiprocessing.get_context('spawn')
    receive,send=ctx.Pipe(duplex=False)
    process=ctx.Process(target=_fetch_child,args=(send,binding,domains),daemon=True)
    try:
        process.start()
        send.close()
        if not receive.poll(timeout):
            raise FetchError('timeout',retry_after=60)
        try:
            result=receive.recv()
        except EOFError:
            raise FetchError('network_error',retry_after=60) from None
        if result[0]=='error':
            raise FetchError(result[1],retry_after=result[2])
        return result[1]
    finally:
        send.close()
        receive.close()
        if process.pid is not None:
            if process.is_alive():
                process.terminate()
            process.join(2)
            if process.is_alive():
                process.kill()
                process.join(2)
            process.close()


def run_once(engine,store,*,registry=PRODUCTION_REGISTRY,fetch=bounded_fetch,now=clock,allow_unattested=False):
    lease=claim(engine,now=now())
    if lease is None:
        return {'state':'idle'}
    try:
        with Session(engine) as db:
            source=db.get(Source,lease.source_id)
            binding=binding_from_db(db,source)
            adapter=registry.resolve(binding,allow_unattested=allow_unattested)
        raw=fetch(binding,adapter.domains)
        store.put(raw.body,raw.payload_hash)
        parsed=adapter.parse(raw,binding)
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
        while True:
            try:
                result=run_once(engine,store)
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
