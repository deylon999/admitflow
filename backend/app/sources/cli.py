"""Local operator commands; no HTTP mutation or arbitrary URL registration."""
import argparse
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..admissions import Source
from ..config import Settings
from ..database import make_engine
from ..jobs import SourceJob, disable, enqueue
from .contracts import AdapterError
from .publishing import binding_from_db
from .registry import PRODUCTION_REGISTRY, runtime_registry
from .status import source_status


def operate(engine,action,source_id,*,registry=PRODUCTION_REGISTRY):
    with Session(engine) as db:
        source=db.get(Source,source_id)
        if source is None:
            raise AdapterError('unsupported_source')
        if action=='status':
            result=source_status(db,source_id,registry=registry)
            job=db.get(SourceJob,source_id)
            result['job']=None if job is None else dict(state=job.state,attempts=job.attempts,nextRunAt=job.next_run_at,lastErrorCode=job.last_error_code)
            return result
        if action=='enqueue':
            registry.resolve(binding_from_db(db,source))
    if action=='enqueue':
        return {'sourceId':source_id,'queued':enqueue(engine,source_id)}
    if action=='disable':
        disable(engine,source_id)
        return {'sourceId':source_id,'enabled':False}
    raise ValueError('unknown_operator_action')


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['list','status','enqueue','disable'])
    parser.add_argument('source_id',nargs='?')
    args=parser.parse_args(argv)
    if args.action!='list' and not args.source_id:
        parser.error('source_id is required')
    engine=make_engine(Settings.from_env().database_url)
    try:
        if args.action=='list':
            with Session(engine) as db:
                result={'items':list(db.scalars(select(Source.id).order_by(Source.id).limit(101)))}
                result['truncated']=len(result['items'])>100
                result['items']=result['items'][:100]
        else:
            result=operate(engine,args.action,args.source_id,registry=runtime_registry())
        print(json.dumps(result,default=lambda value:value.isoformat()),flush=True)
        return 0
    except AdapterError as error:
        print(json.dumps({'error':error.code}),flush=True)
        return 1
    except Exception:
        print(json.dumps({'error':'operation_failed'}),flush=True)
        return 1
    finally:
        engine.dispose()


if __name__=='__main__':
    raise SystemExit(main())
