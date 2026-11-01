"""Dry-run by default; retain every raw hash referenced by immutable DB history."""
import argparse
from datetime import datetime, timedelta, timezone
import json
import os
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..admissions import SourceSnapshot
from ..config import Settings
from ..database import make_engine
from .storage import RawStore


def cleanup_raw(engine,store,*,days=7,apply=False,now=None):
    if not 1 <= days <= 365:
        raise ValueError('invalid_retention_days')
    cutoff=((now or datetime.now(timezone.utc))-timedelta(days=days)).timestamp()
    result=dict(candidates=0,deleted=0,retained=0,skipped=0,dryRun=not apply)
    with store.locked():
        # Failure to read references must happen before considering any deletion.
        with Session(engine) as db:
            referenced=set(db.scalars(select(SourceSnapshot.payload_hash)))
        for path in sorted(store.root.iterdir()):
            if not re.fullmatch('[a-f0-9]{64}',path.name):
                continue
            if path.is_symlink() or not path.is_file():
                result['skipped']+=1
                continue
            if path.name in referenced or path.stat().st_mtime>cutoff:
                result['retained']+=1
                continue
            target=store._path(path.name)
            result['candidates']+=1
            if apply:
                target.unlink()
                result['deleted']+=1
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--days',type=int,default=7)
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args(argv)
    engine=make_engine(Settings.from_env().database_url)
    try:
        result=cleanup_raw(engine,RawStore(os.getenv('RAW_STORE_PATH','./var/raw')),days=args.days,apply=args.apply)
        print(json.dumps(result))
        return 0
    except Exception:
        print(json.dumps({'error':'retention_failed','partialDeletionPossible':args.apply}))
        return 1
    finally:
        engine.dispose()


if __name__=='__main__':
    raise SystemExit(main())
