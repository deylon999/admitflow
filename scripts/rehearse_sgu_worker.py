#!/usr/bin/env python3
"""Run one real archive-source worker fetch in an owned PostgreSQL runtime."""
import argparse
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile

from postgres_runtime import disposable_postgres

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/tests')]
from sqlalchemy import func,select
from sqlalchemy.orm import Session
from app.admissions import CandidateEntry,PublishedSnapshot,SourceSnapshot
from app.database import make_engine
from app.jobs import SourceJob,enqueue
from app.migrations import upgrade_schema
from app.sources.adapters.sgu2026 import SOURCE_ID
from app.sources.storage import RawStore
from sgu_helpers import seed_sgu


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--replay-original',type=Path,help='Verify current worker code against a private original without another HTTP request')
    args=p.parse_args()
    with tempfile.TemporaryDirectory(prefix='admitflow-sgu-worker-') as folder:
        with disposable_postgres() as runtime:
            engine=make_engine(runtime.url())
            try:
                upgrade_schema(engine);seed_sgu(engine)
                enqueue(engine,SOURCE_ID,interval_seconds=900)
                env={**os.environ,'DATABASE_URL':runtime.url(),'SOURCE_IDENTITY_KEY':secrets.token_hex(32),'RAW_STORE_PATH':str(Path(folder)/'raw')}
                def once(replay=False):
                    command=[sys.executable,'-m','app.worker','once']
                    if replay:
                        env['ARCHIVE_REPLAY_PATH']=str(args.replay_original.resolve())
                        command=[sys.executable,'-c','''
import hashlib,json,os
from datetime import datetime,timezone
from app.config import Settings
from app.database import make_engine
from app.sources.registry import runtime_registry
from app.sources.fetcher import FetchResult
from app.sources.storage import RawStore
from app.worker import run_once
def replay(binding,domains,**options):
    with open(os.environ['ARCHIVE_REPLAY_PATH'],'rb') as file:body=file.read(8*1024*1024+1)
    return FetchResult(binding.url,body,'text/html',hashlib.sha256(body).hexdigest(),datetime.now(timezone.utc),'utf-8')
engine=make_engine(Settings.from_env().database_url)
try:print(json.dumps(run_once(engine,RawStore(os.environ['RAW_STORE_PATH']),registry=runtime_registry(),fetch=replay)))
finally:engine.dispose()
''']
                    result=subprocess.run(command,cwd=ROOT/'backend',env=env,capture_output=True,text=True,timeout=75)
                    if result.returncode!=0:raise RuntimeError('Actual SGU worker refused; no payload/key details emitted')
                    return json.loads(result.stdout)
                first=once(bool(args.replay_original));second=once()
                if first.get('state')!='success' or second.get('state')!='idle':raise RuntimeError('Worker scheduling outcomes differ')
                with Session(engine) as db:
                    snapshot=db.get(SourceSnapshot,db.get(PublishedSnapshot,SOURCE_ID).snapshot_id)
                    raw=RawStore(env['RAW_STORE_PATH']).read(snapshot.payload_hash)
                    rows=db.scalar(select(func.count()).select_from(CandidateEntry))
                    job=db.get(SourceJob,SOURCE_ID)
                    if rows!=573 or job.state!='idle' or snapshot.kind!='archive' or snapshot.seats!=16:raise RuntimeError('Published archive fields differ')
                    report=dict(recordedAt=datetime.now(timezone.utc).isoformat(),success=True,actualWorkerProcesses=2,
                                transport='private original replay' if args.replay_original else 'HTTPS',
                                outcomes=[first['state'],second['state']],sourceId=SOURCE_ID,kind=snapshot.kind,
                                rows=rows,seats=snapshot.seats,sourceUpdatedAt=None,rawBytes=len(raw),rawSha256=snapshot.payload_hash,
                                intervalSeconds=job.interval_seconds,sourceSnapshots=db.scalar(select(func.count()).select_from(SourceSnapshot)),
                                fetchedAt=snapshot.fetched_at.isoformat(),scope=('private original replay,no HTTP' if args.replay_original else 'one actual archive HTTP cycle')+';second process idle;not24h live-soak or automated admission assessment')
            finally:engine.dispose()
    report['cleanup']=True;args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))


if __name__=='__main__':main()
