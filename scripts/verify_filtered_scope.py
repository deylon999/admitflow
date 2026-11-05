"""Actual bounded HTTPS -> worker -> disposable PostgreSQL -> independent audit."""
import argparse,json,os,secrets,sys,tempfile
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/tests')]
from sqlalchemy import func,select
from sqlalchemy.orm import Session
from pg_support import isolated_postgres
from app.admissions import CandidateEntry,SourceSnapshot
from app.coverage import coverage
from app.jobs import enqueue
from app.migrations import upgrade_schema
from app.sources.audit import audit_source
from app.sources.profile_registration import register_profile
from app.sources.registry import runtime_registry
from app.sources.storage import RawStore
from app.sources.table_profiles import PROFILES
from app.worker import run_once,bounded_fetch
from review_bgu_scope import compare_rows


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'docs/evidence/b17-bgu-runtime.json');args=parser.parse_args()
    profile=PROFILES['bgu-2026-080301-contract'];secret=secrets.token_bytes(32);os.environ['SOURCE_IDENTITY_KEY']=secret.hex()
    registry=runtime_registry();captured=[]
    def fetch(binding,domains,**kwargs):
        raw=bounded_fetch(binding,domains,**kwargs)
        audit=compare_rows(raw.body,profile,registry.resolve(binding).parse(raw,binding),secret)
        captured.append(dict(payloadHash=raw.payload_hash,originalAuditHashMatched=raw.payload_hash==profile.proof.original_sha256,**audit))
        return raw
    with isolated_postgres(os.environ.get('TEST_DATABASE_URL','')) as engine,tempfile.TemporaryDirectory(prefix='admitflow-filtered-') as folder:
        upgrade_schema(engine);store=RawStore(Path(folder)/'raw')
        register_profile(engine,profile,enable=True,registry=registry);assert enqueue(engine,profile.source_id)
        outcome=run_once(engine,store,registry=registry,fetch=fetch)
        if outcome['state']!='success':raise RuntimeError('filtered source worker failed')
        audit=audit_source(engine,store,profile.source_id,registry=registry)
        assert audit['success'] and audit['checkedRows']==109
        with Session(engine) as db:
            rows=db.scalar(select(func.count()).select_from(CandidateEntry));snapshots=db.scalar(select(func.count()).select_from(SourceSnapshot))
            counts=coverage(db,registry=registry)
        assert rows==109 and snapshots==1 and len(captured)==1
        assert counts['importedGroups']==counts['importedUniversities']==counts['archiveImportedGroups']==1
        assert counts['catalogUniversities']==1257 and counts['freshGroups']==counts['conditionalGroups']==counts['automaticSources']==0
        report=dict(checkedAt=datetime.now(timezone.utc).isoformat(),sourceId=profile.source_id,version=profile.version,
            externalHttpsFetches=1,workerState='success',rows=rows,snapshots=snapshots,seats=profile.seats,kind='archive',
            independentCurrentOriginalAudit=captured[0],storedAuditSuccess=True,archiveImportedGroups=1,importedUniversities=1,
            freshGroups=0,conditionalGroups=0,nationalTotal=None,ownerPathUsesSyntheticFixtureOnly=True,
            candidateValuesOrKeysExported=False,disposableSchemaRemoved=True,userDatabaseChanged=False)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))


if __name__=='__main__':main()
