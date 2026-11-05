"""Real HTTPS -> worker -> disposable PostgreSQL -> independent/offline audit.

Linux only. TEST_DATABASE_URL must name an admitflow_test* database. Raw bodies
and the temporary identity key never appear in the aggregate output.
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
from sqlalchemy import select,func
from sqlalchemy.orm import Session
from pg_support import isolated_postgres
from app.admissions import CandidateEntry,SourceSnapshot
from app.catalog import catalog_size
from app.coverage import coverage
from app.jobs import enqueue
from app.migrations import upgrade_schema
from app.sources.audit import audit_source
from app.sources.profile_registration import register_profile
from app.sources.page_cache import PageFetchCache
from app.sources.registry import runtime_registry
from app.sources.storage import RawStore
from app.sources.table_family import SECTION_VERSION
from app.sources.table_profiles import PROFILES
from app.worker import run_once,bounded_fetch
from review_section_family import compare_rows


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'docs/evidence/b15-section-family-runtime.json')
    parser.add_argument('--all-profiles',action='store_true')
    parser.add_argument('--page-cache',action='store_true')
    args=parser.parse_args();scopes=[p for p in PROFILES.values() if args.all_profiles or p.version==SECTION_VERSION]
    secret=secrets.token_bytes(32);os.environ['SOURCE_IDENTITY_KEY']=secret.hex();registry=runtime_registry()
    originals={};checked=[];external=[]
    def transport(binding,domains,**kwargs):
        raw=bounded_fetch(binding,domains,**kwargs);external.append(binding.url);return raw
    cache=PageFetchCache(transport)
    def fetch(binding,domains,**kwargs):
        # Without --page-cache the evidence runner shares each original itself;
        # with it, exercise the production worker cache and its original clock.
        if args.page_cache:raw=cache(binding,domains,**kwargs)
        else:
            if binding.url not in originals:originals[binding.url]=transport(binding,domains,**kwargs)
            raw=originals[binding.url]
        p=PROFILES[binding.source_id]
        parsed=registry.resolve(binding).parse(raw,binding)
        if p.version==SECTION_VERSION:compare_rows(raw.body,p,parsed,secret)
        checked.append(dict(sourceId=p.source_id,rows=p.rows,payloadHash=raw.payload_hash,
            originalAuditHashMatched=raw.payload_hash==p.proof.original_sha256))
        return raw
    with isolated_postgres(os.environ.get('TEST_DATABASE_URL','')) as engine,tempfile.TemporaryDirectory(prefix='admitflow-section-') as folder:
        upgrade_schema(engine);store=RawStore(Path(folder)/'raw')
        for p in scopes:
            register_profile(engine,p,enable=True,registry=registry)
            if args.all_profiles and dict(p.catalog)['funding']=='budget':
                from app.scenario_storage import enable_scenarios
                enable_scenarios(engine,p.source_id,registry=registry)
            assert enqueue(engine,p.source_id)
        for _ in scopes:
            if run_once(engine,store,registry=registry,fetch=fetch)['state']!='success':raise RuntimeError('section worker failed')
        for p in scopes:
            if not audit_source(engine,store,p.source_id,registry=registry)['success']:raise RuntimeError('stored section audit failed')
        with Session(engine) as db:
            rows=db.scalar(select(func.count()).select_from(CandidateEntry));snapshots=db.scalar(select(func.count()).select_from(SourceSnapshot))
            counts=coverage(db,registry=registry);catalog=catalog_size(db)
        expected_rows=sum(p.rows for p in scopes);expected_pages=len({p.url for p in scopes})
        expected_universities=len({dict(p.catalog)['university_id'] for p in scopes})
        assert rows==expected_rows and snapshots==len(scopes) and len(external)==expected_pages and len(checked)==len(scopes)
        assert catalog==1257 and counts['importedUniversities']==expected_universities and counts['archiveImportedGroups']==len(scopes)
        assert counts['automaticSources']==counts['freshGroups']==0
        assert counts['conditionalGroups']==(2 if args.all_profiles else 0)
        if args.page_cache:assert cache.hits==len(scopes)-expected_pages
        result=dict(checkedAt=datetime.now(timezone.utc).isoformat(),versions=sorted({p.version for p in scopes}),externalHttpsFetches=len(external),
            scopes=len(checked),rows=rows,snapshots=snapshots,kind='archive',independentOriginalRowsChecked=sum(p.rows for p in scopes if p.version==SECTION_VERSION),
            independentlyRecheckedSectionRows=sum(p.rows for p in scopes if p.version==SECTION_VERSION),
            storedAuditsPassed=True,catalogUniversities=catalog,importedUniversities=expected_universities,archiveImportedGroups=len(scopes),
            freshGroups=0,automaticSources=0,conditionalGroups=counts['conditionalGroups'],nationalTotal=None,checks=checked,
            processLocalCacheEnabled=args.page_cache,cacheHits=cache.hits,cacheMisses=cache.misses,
            disposableSchemaRemoved=True,userDatabaseChanged=False)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='checks'}))


if __name__=='__main__':main()
