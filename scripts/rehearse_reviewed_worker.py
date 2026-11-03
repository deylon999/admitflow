#!/usr/bin/env python3
"""One real HTTP worker cycle for a reviewed source,in disposable PostgreSQL."""
import argparse
from datetime import datetime,timezone
import json,os,secrets,subprocess,sys,tempfile
from pathlib import Path
from postgres_runtime import disposable_postgres
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from sqlalchemy import func,select
from sqlalchemy.orm import Session
from app.admissions import CandidateEntry,SourceSnapshot,PublishedSnapshot
from app.database import make_engine
from app.jobs import enqueue
from app.migrations import upgrade_schema
from app.sources.table_profiles import PROFILES
from app.sources.profile_registration import register_profile
from app.sources.registry import runtime_registry
from app.sources.storage import RawStore


def main():
    p=argparse.ArgumentParser();p.add_argument('profile',choices=list(PROFILES));p.add_argument('--output',type=Path,required=True);p.add_argument('--capture-directory',type=Path);a=p.parse_args();profile=PROFILES[a.profile]
    os.environ['SOURCE_IDENTITY_KEY']=secrets.token_hex(32)
    with tempfile.TemporaryDirectory(prefix='admitflow-reviewed-worker-') as folder,disposable_postgres() as runtime:
        engine=make_engine(runtime.url())
        try:
            upgrade_schema(engine);registry=runtime_registry();register_profile(engine,profile,enable=True,registry=registry);enqueue(engine,profile.source_id)
            env={**os.environ,'DATABASE_URL':runtime.url(),'RAW_STORE_PATH':str(Path(folder)/'raw')}
            results=[]
            for _ in range(2):
                run=subprocess.run([sys.executable,'-m','app.worker','once'],cwd=ROOT/'backend',env=env,capture_output=True,text=True,timeout=75)
                if run.returncode:raise RuntimeError('Reviewed worker cycle refused;details/key/raw withheld')
                results.append(json.loads(run.stdout))
            assert [x['state'] for x in results]==['success','idle']
            with Session(engine) as db:
                snapshot=db.get(SourceSnapshot,db.get(PublishedSnapshot,profile.source_id).snapshot_id)
                body=RawStore(env['RAW_STORE_PATH']).read(snapshot.payload_hash)
                assert db.scalar(select(func.count()).select_from(CandidateEntry))==profile.rows
                report={'recordedAt':datetime.now(timezone.utc).isoformat(),'success':True,'sourceId':profile.source_id,'url':profile.url,'kind':'archive','year':profile.year,'rows':profile.rows,'places':snapshot.seats,'fetchedAt':snapshot.fetched_at.isoformat(),'sourceUpdatedAt':None,'rawBytes':len(body),'rawSha256':snapshot.payload_hash,'outcomes':[x['state'] for x in results],'workerProcesses':2,'externalHttpFetches':1,'scope':'one actual HTTP/nativePG archive cycle,secondprocessidle;not24h live observation'}
                if a.capture_directory:
                    a.capture_directory.mkdir(parents=True,mode=0o700,exist_ok=False)
                    for name,value in [('response.bin',body),('manifest.json',json.dumps({'profile':profile.source_id,'url':profile.url,'fetchedAt':snapshot.fetched_at.isoformat(),'payloadHash':snapshot.payload_hash,'contentType':snapshot.content_type,'charset':snapshot.charset,'bytes':len(body)}).encode())]:
                        with os.fdopen(os.open(a.capture_directory/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as file:file.write(value)
        finally:engine.dispose()
    report['cleanup']=True;a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))


if __name__=='__main__':main()
