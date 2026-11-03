"""Operator-only offline integrity check; emits aggregates and safe codes."""
import argparse
from contextlib import contextmanager
import json
import os
from urllib.parse import urlsplit
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..admissions import Campaign,CompetitionGroup,PublishedSnapshot,Source,SourceSnapshot
from ..config import Settings
from ..diagnostics import read_engine
from .contracts import AdapterError,SourceBinding
from .fetcher import FetchResult
from .publishing import stored_list,utc
from .registry import PRODUCTION_REGISTRY,runtime_registry
from .storage import RawStore,StorageError
from .validation import Quarantined,validate_list


@contextmanager
def readonly_connection(engine):
    with engine.connect() as connection:
        previous=None
        try:
            if engine.dialect.name=='postgresql':
                connection.exec_driver_sql('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
                connection.exec_driver_sql("SET LOCAL statement_timeout = '5000ms'")
                connection.exec_driver_sql("SET LOCAL lock_timeout = '2000ms'")
            else:
                previous=connection.exec_driver_sql('PRAGMA query_only').scalar();connection.rollback()
                connection.exec_driver_sql('PRAGMA query_only=ON');connection.exec_driver_sql('BEGIN')
            yield connection
        finally:
            connection.rollback()
            if previous is not None:
                connection.exec_driver_sql(f'PRAGMA query_only={int(previous)}');connection.rollback()


def audit_source(engine,store,source_id,*,registry=PRODUCTION_REGISTRY,limit=100):
    if type(limit) is not int or not 1<=limit<=100:raise ValueError('invalid_audit_limit')
    report={'format':'source-audit-v1','sourceId':source_id,'readOnly':True,'externalFetches':0,'checkedSnapshots':0,'checkedRows':0,'issues':[],'truncated':False}
    with store.locked(),readonly_connection(engine) as connection:
        with Session(bind=connection) as db:
            source=db.get(Source,source_id)
            if source is None:raise AdapterError('unsupported_source')
            group=db.get(CompetitionGroup,source.group_id);campaign=db.get(Campaign,group.campaign_id)
            snapshots=db.scalars(select(SourceSnapshot).where(SourceSnapshot.source_id==source_id).order_by(SourceSnapshot.fetched_at,SourceSnapshot.id).limit(limit+1)).all()
            report['truncated']=len(snapshots)>limit
            pointer=db.get(PublishedSnapshot,source_id)
            report['publishedSnapshotId']=pointer.snapshot_id if pointer else None
            if pointer is None:report['issues'].append({'code':'missing_published_pointer'})
            for snapshot in snapshots[:limit]:
                code=None
                try:
                    # Enabled=True is solely an offline adapter permission; no
                    # source row changes or network transport exists in this module.
                    binding=SourceBinding(source_id,group.id,campaign.year,snapshot.fetched_url or source.url,
                        urlsplit(snapshot.fetched_url or source.url).hostname,snapshot.adapter_version or '',snapshot.kind,True)
                    adapter=registry.resolve(binding)
                    body=store.read(snapshot.payload_hash)
                    if len(body)>adapter.max_bytes:raise StorageError('raw_size_invalid')
                    raw=FetchResult(binding.url,body,snapshot.content_type or 'text/html',snapshot.payload_hash,utc(snapshot.fetched_at),snapshot.charset)
                    parsed=adapter.parse(raw,binding)
                    rebuilt=validate_list(parsed,binding,raw.fetched_at)
                    stored=validate_list(stored_list(db,snapshot,campaign.year),binding,raw.fetched_at)
                    # PostgreSQL Numeric preserves scale (299 -> 299.00).
                    # Compare stored decimal values semantically; the original
                    # parser output still must match its exact published hash.
                    if rebuilt.normalized_hash!=snapshot.normalized_hash:code='normalized_hash_mismatch'
                    elif stored.parsed!=rebuilt.parsed:code='stored_facts_mismatch'
                    else:report['checkedRows']+=len(parsed.entries)
                except (StorageError,AdapterError,Quarantined) as error:code=error.code
                except Exception:code='audit_failed'
                report['checkedSnapshots']+=1
                if code:report['issues'].append({'snapshotId':snapshot.id,'code':code})
            if not snapshots:report['issues'].append({'code':'no_snapshots'})
            if pointer and not db.scalar(select(SourceSnapshot.id).where(SourceSnapshot.id==pointer.snapshot_id,SourceSnapshot.source_id==source_id)):
                report['issues'].append({'code':'invalid_published_pointer'})
    report['success']=not report['issues'] and not report['truncated'];return report


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source_id');p.add_argument('--limit',type=int,default=100);args=p.parse_args(argv)
    engine=None
    try:
        engine=read_engine(Settings.from_env().database_url)
        root=os.getenv('RAW_STORE_PATH','./var/raw')
        from pathlib import Path
        if not Path(root).is_dir():raise StorageError('raw_unavailable')
        result=audit_source(engine,RawStore(root),args.source_id,registry=runtime_registry(),limit=args.limit)
        print(json.dumps(result));return 0 if result['success'] else 1
    except (AdapterError,StorageError) as error:print(json.dumps({'success':False,'code':error.code}));return 1
    except Exception:print(json.dumps({'success':False,'code':'audit_failed'}));return 1
    finally:
        if engine is not None:engine.dispose()


if __name__=='__main__':raise SystemExit(main())
