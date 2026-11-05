"""Actual HTTPS -> bounded child -> worker -> isolated PG -> offline audit.

Linux only. Requires TEST_DATABASE_URL with disposable admitflow_test* DB.
Never enables sources in a user database; the newly created schema is removed.
"""
import argparse
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import secrets
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/tests')]
from pg_support import isolated_postgres
from sqlalchemy import select,func
from sqlalchemy.orm import Session
from app.admissions import CandidateEntry,SourceSnapshot
from app.jobs import enqueue
from app.migrations import upgrade_schema
from app.sources.audit import audit_source
from app.sources.profile_registration import register_profile
from app.sources.registry import runtime_registry
from app.sources.storage import RawStore
from app.sources.table_profiles import PROFILES
from app.worker import run_once,bounded_fetch
from review_sgu_scope import audit_rows


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'docs/evidence/b14-sgu4576-runtime.json')
    args=parser.parse_args();profile=PROFILES['sgu-2026-4576']
    secret=secrets.token_bytes(32);os.environ['SOURCE_IDENTITY_KEY']=secret.hex();registry=runtime_registry()
    captured=[]
    def fetch(binding,domains,**kwargs):
        raw=bounded_fetch(binding,domains,**kwargs)
        parsed=registry.resolve(binding).parse(raw,binding)
        audit_rows(raw.body,parsed,secret)
        captured.append(raw.payload_hash)
        return raw
    with isolated_postgres(os.environ.get('TEST_DATABASE_URL','')) as engine,tempfile.TemporaryDirectory(prefix='admitflow-scope-') as folder:
        upgrade_schema(engine);store=RawStore(Path(folder)/'raw')
        register_profile(engine,profile,enable=True,registry=registry)
        assert enqueue(engine,profile.source_id)
        outcome=run_once(engine,store,registry=registry,fetch=fetch)
        if outcome['state']!='success':raise RuntimeError('reviewed scope worker did not succeed')
        audit=audit_source(engine,store,profile.source_id,registry=registry)
        if not audit['success']:raise RuntimeError('stored scope integrity check failed')
        with Session(engine) as db:
            rows=db.scalar(select(func.count()).select_from(CandidateEntry));snapshots=db.scalar(select(func.count()).select_from(SourceSnapshot))
        assert rows==453 and snapshots==1 and audit['checkedRows']==453
        report=dict(sourceId=profile.source_id,checkedAt=datetime.now(timezone.utc).isoformat(),externalHttpsFetches=1,
            workerState=outcome['state'],rows=rows,seats=profile.seats,snapshots=snapshots,kind='archive',
            independentOriginalRowsChecked=453,storedAuditSuccess=audit['success'],payloadHash=captured[0],
            originalAuditHashMatched=captured[0]==profile.proof.original_sha256,disposableSchemaRemoved=True,userDatabaseChanged=False)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))


if __name__=='__main__':main()
