"""Measure the real catalog facade on synthetic data in owned PostgreSQL only.

Never reads DATABASE_URL, captures official data, or publishes outside the
temporary schema. The generated records are not national coverage evidence.
Run with the backend Python: scripts/qa/benchmark_product_catalog.py --output ...
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import gc
import hashlib
import json
import math
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time
import tracemalloc

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'backend'), str(ROOT/'backend/tests'), str(ROOT)]

from sqlalchemy import event, insert, select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.accreditation_registry import load_registry
from app.admissions import Campaign, University
from app.catalog_import import import_reviewed
from app.config import Settings
from app.main import create_app
from app.migrations import upgrade_schema
from app.national_catalog import load_catalog
from app.product_catalog import program_page
from pg_support import isolated_postgres
from scripts.ops.postgres_runtime import disposable_postgres


def seed(engine, *, heads=785, branches=215, per_campaign=25, history=2):
    """Bulk synthetic fixture, with all normal FK/check/immutability guards on."""
    catalog = load_catalog().institutions
    head_ids = [r.id for r in catalog if not r.is_branch and r.id != 'sgu-saratov']
    head_ids += [r.id for r in load_registry().registry_only]
    ids = head_ids[:heads] + [r.id for r in catalog if r.is_branch][:branches]
    if len(ids) != heads+branches:
        raise ValueError('fixture exceeds known organization scope')
    now = datetime(2026, 11, 22, tzinfo=timezone.utc)
    with engine.begin() as db:
        db.execute(insert(University), [dict(id=uid, name=f'Synthetic scale university {i:04}',
            parent_id=ids[0] if i >= heads else None, region='Synthetic only',
            official_url='https://synthetic.invalid/scale', provenance_url='https://synthetic.invalid/scale',
            verified_at=now) for i,uid in enumerate(ids)])
        campaigns = [dict(id=hashlib.md5(f'scale:{uid}:{year}'.encode()).hexdigest(), university_id=uid,
            year=year, level='specialist' if i%4==0 else 'bachelor')
            for i,uid in enumerate(ids) for year in range(2024,2028)]
        db.execute(insert(Campaign), campaigns)
        db.execute(text("""CREATE TEMP TABLE scale_keys ON COMMIT DROP AS
            SELECT md5('program:'||c.id||':'||k) pid, c.id cid, c.university_id uid, c.year, c.level,
                'scale-'||k source_key, md5('public:'||c.id||':'||k) public_id, k
            FROM campaigns c CROSS JOIN generate_series(1,:per) k
            WHERE c.university_id != 'sgu-saratov'"""), {'per':per_campaign})
        db.execute(text("""INSERT INTO programs(id,university_id,level,origin_campaign_id,source_namespace,source_key)
            SELECT pid,uid,level,cid,'synthetic-scale-v1',source_key FROM scale_keys"""))
        db.execute(text("""INSERT INTO campaign_programs(program_id,campaign_id,university_id,level)
            SELECT pid,cid,uid,level FROM scale_keys"""))
        db.execute(text("""INSERT INTO program_catalog_documents(id,campaign_id,source_namespace)
            SELECT md5('doc:'||id),id,'synthetic-scale-v1' FROM campaigns WHERE university_id != 'sgu-saratov'"""))
        db.execute(text("""INSERT INTO program_catalog_revisions
            (id,document_id,campaign_id,original_url,final_url,content_type,document_type,verification_status,
             fetched_at,checked_at,original_sha256,extractor_version,review_sha256,normalized_sha256,
             completeness,program_count,group_count,university_name)
            SELECT md5(d.id||':rev:'||v),d.id,d.campaign_id,'https://synthetic.invalid/scale',
                'https://synthetic.invalid/scale','text/html','synthetic-benchmark','verified',
                :now,:now,repeat(md5(d.id||v),2),'synthetic-scale-v1',repeat(md5(d.id||v),2),
                repeat(md5(d.id||v),2),'partial',:per,0,u.name
            FROM program_catalog_documents d JOIN campaigns c ON c.id=d.campaign_id
                JOIN universities u ON u.id=c.university_id CROSS JOIN generate_series(0,:history) v"""),
            {'now':now,'per':per_campaign,'history':history})
        db.execute(text("""INSERT INTO program_catalog_facts
            (revision_id,program_id,campaign_id,public_id,source_key,title,code,study_form,funding,
             category,seats,evidence,search_text,sort_text)
            SELECT r.id,k.pid,k.cid,k.public_id,k.source_key,
                'Synthetic Программа Straße ΟΣ Ёж 100%_ '||
                    CASE WHEN k.k=1 THEN 'уникальный ' ELSE '' END||k.source_key||' '||k.cid,
                CASE WHEN k.k%7=0 THEN '40.05.01' ELSE '09.03.04' END,
                CASE WHEN k.k%3=0 THEN NULL ELSE 'full-time' END,NULL,NULL,NULL,
                json_build_object('synthetic',true),
                'synthetic программа strasse οσ ёж 100%_ '||
                    CASE WHEN k.k%7=0 THEN '40.05.01 ' ELSE '09.03.04 ' END||
                    CASE WHEN k.k=1 THEN 'уникальный ' ELSE '' END||k.source_key||' '||k.cid||' '||lower(r.university_name),
                'synthetic программа strasse οσ ёж 100%_ '||
                    CASE WHEN k.k=1 THEN 'уникальный ' ELSE '' END||k.source_key||' '||k.cid
            FROM scale_keys k JOIN program_catalog_revisions r ON r.campaign_id=k.cid"""))
        db.execute(text("""INSERT INTO program_catalog_publications(document_id,revision_id)
            SELECT d.id,md5(d.id||':rev:'||:history) FROM program_catalog_documents d"""),{'history':str(history)})
        db.execute(text('ANALYZE'))
    return dict(synthetic=True,heads=heads,branches=branches,years=[2024,2025,2026,2027],
        currentPrograms=len(campaigns)*per_campaign,previousFactVersions=len(campaigns)*per_campaign*history,
        currentDocuments=len(campaigns),newCompetitionGroups=0,sampleUniversity=ids[0])


def percentile(values, p):
    return sorted(values)[max(0,math.ceil(len(values)*p)-1)]


def measure(engine, params, repeats, timeout_ms):
    statements=[]
    def query(conn,cursor,statement,parameters,context,executemany):
        statements.append((statement,parameters))
    def run():
        with Session(engine) as db:
            db.execute(text(f'SET LOCAL statement_timeout={timeout_ms}'))
            return program_page(db,**params)
    event.listen(engine,'before_cursor_execute',query)
    start=time.perf_counter()
    try:
        run()  # warm caches and mapper metadata before timing
    except DBAPIError as error:
        if getattr(error.orig,'sqlstate',None)!='57014':
            raise
        sql,parameters=statements[-1]
        with engine.connect() as db:
            plan=db.exec_driver_sql('EXPLAIN (FORMAT JSON) '+sql,parameters).scalar()
        return dict(params=params,timedOut=True,statementTimeoutMs=timeout_ms,
            elapsedMs=(time.perf_counter()-start)*1000,plans=[dict(sql=sql,plan=plan,analyze=False)])
    finally:
        event.remove(engine,'before_cursor_execute',query)
    statements.clear()
    samples=[]
    for _ in range(repeats):
        start=time.perf_counter()
        result=run()
        samples.append((time.perf_counter()-start)*1000)
    hydrated=Counter()
    def loaded(session,obj): hydrated[type(obj).__name__]+=1
    event.listen(engine,'before_cursor_execute',query)
    event.listen(Session,'loaded_as_persistent',loaded)
    gc.collect()
    tracemalloc.start()
    try:
        result=run()
        _,peak=tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
        event.remove(engine,'before_cursor_execute',query)
        event.remove(Session,'loaded_as_persistent',loaded)
    plans=[]
    with engine.connect() as db:
        db.execute(text(f'SET LOCAL statement_timeout={timeout_ms}'))
        for sql,parameters in statements:
            if 'count(*)' in sql.lower() or ('LIMIT' in sql and 'program_catalog_facts' in sql):
                plan=db.exec_driver_sql('EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) '+sql,parameters).scalar()
                plans.append(dict(sql=sql,plan=plan))
    digest=hashlib.sha256(json.dumps(result.model_dump(mode='json'),ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    return dict(params=params,total=result.total,items=len(result.items),nextOffset=result.next_offset,responseSha256=digest,
        years=result.years,latencyMs=dict(samples=samples,p50=statistics.median(samples),p95=percentile(samples,.95)),
        pythonPeakBytes=peak,sqlStatements=len(statements),hydratedObjects=dict(hydrated),plans=plans)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--per-campaign',type=int,default=25)
    parser.add_argument('--heads',type=int,default=785)
    parser.add_argument('--branches',type=int,default=215)
    parser.add_argument('--history',type=int,default=2)
    parser.add_argument('--repeats',type=int,default=9)
    parser.add_argument('--statement-timeout-ms',type=int,default=10000)
    args=parser.parse_args(argv)
    if not (1<=args.per_campaign<=1000 and 1<=args.heads<=785 and 0<=args.branches<=215
            and 0<=args.history<=5 and 3<=args.repeats<=100 and 1000<=args.statement_timeout_ms<=60000):
        parser.error('benchmark dimensions outside bounded synthetic profile')
    report=dict(generatedAt=datetime.now(timezone.utc).isoformat(),sourceCommit=subprocess.check_output(
        ['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),platform=platform.platform(),python=platform.python_version(),
        dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True)),
        scope='owned disposable PostgreSQL, synthetic only; no staging or national coverage claim')
    with disposable_postgres() as runtime, isolated_postgres(runtime.url()) as engine:
        upgrade_schema(engine)
        import_reviewed(engine)
        print('Seeding synthetic catalogue...',flush=True)
        report['fixture']=seed(engine,heads=args.heads,branches=args.branches,
            per_campaign=args.per_campaign,history=args.history)
        with engine.connect() as db:
            report.update(postgresVersion=db.scalar(text('SHOW server_version')),
                schemaRevision=db.scalar(text('SELECT version_num FROM alembic_version')),
                workMem=db.scalar(text('SHOW work_mem')))
        uid=report['fixture']['sampleUniversity']
        cases=dict(first={},year={'year':2027},university={'university_id':uid,'year':2027},
            code={'q':'09.03.04','year':2027},selective={'q':'уникальный','year':2027},
            missing={'q':'absolutely-missing'},deep={'offset':max(0,report['fixture']['currentPrograms']-12)},
            descending={'sort':'name-desc','limit':50})
        report['cases']={}
        for name,params in cases.items():
            print('Measuring '+name,flush=True)
            report['cases'][name]=measure(engine,params,args.repeats,args.statement_timeout_ms)
            args.output.parent.mkdir(parents=True,exist_ok=True)
            args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        url=engine.url.update_query_dict({'options':engine.url.query['options']+f' -cstatement_timeout={args.statement_timeout_ms}'})
        app=create_app(Settings(database_url=url.render_as_string(hide_password=False),auto_create_schema=False))
        with TestClient(app,raise_server_exceptions=False) as client:
            report['http']={}
            for path,params in [('/programs',{'year':2027,'limit':12}),('/programs/sgu-2026-4588',{}),
                    ('/universities',{'q':'уникальный'}),('/universities/'+uid,{})]:
                start=time.perf_counter()
                response=client.get('/api/v1/catalog'+path,params=params)
                body=response.json() if response.status_code==200 else {}
                report['http'][path]=dict(status=response.status_code,latencyMs=(time.perf_counter()-start)*1000,
                    total=body.get('total'),seats=body.get('seats'),knownProgramCount=body.get('knownProgramCount'))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Report: '+str(args.output),flush=True)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
