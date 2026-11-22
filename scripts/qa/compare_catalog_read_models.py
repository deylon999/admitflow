"""Experimental read architectures; owned synthetic PostgreSQL, never publication.

Prepared tables here are frozen benchmark prototypes, not a production cache.
Transactional maintenance and correctness tests are required before adoption.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import math
from pathlib import Path
import statistics
import subprocess
import sys
import threading
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'backend'),str(ROOT/'backend/tests')]
from sqlalchemy import MetaData, Table, exists, literal, select, text, union_all
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
import app.catalog.product_catalog as facade
from app.catalog.program_catalog_models import ProgramCatalogFact as Fact, ProgramCatalogRevision as Revision, ProgramCatalogPublication as Publication
from app.admissions import Campaign
from app.catalog.catalog_import import import_reviewed
from app.catalog.national_catalog import load_catalog
from app.catalog.accreditation_registry import load_registry
from app.config import Settings
from app.main import create_app
from app.migrations import upgrade_schema
from pg_support import isolated_postgres
from scripts.ops.postgres_runtime import disposable_postgres
from scripts.qa.benchmark_product_catalog import seed, measure
import scripts.qa.benchmark_product_catalog as benchmark


def direct_page(db, *, q='', university_id='', year=None, subject='', offset=0, limit=12, sort='name'):
    index,legacy=facade.program_index(db)
    query=select(index)
    if university_id:query=query.where(index.c.university_id==university_id)
    scope=query.subquery()
    years=list(db.scalars(select(scope.c.year).distinct().order_by(scope.c.year.desc())))
    if year is not None:query=query.where(index.c.year==year)
    if subject:query=query.where(literal(False))
    for token in q.casefold().split():query=query.where(index.c.search_text.contains(token,autoescape=True))
    total=db.scalar(select(facade.func.count()).select_from(query.subquery()))
    order=(index.c.sort_text.desc(),index.c.id.desc()) if sort=='name-desc' else (index.c.sort_text,index.c.id)
    keys=db.execute(query.with_only_columns(index.c.id,index.c.pid,index.c.rid).order_by(*order).offset(offset).limit(limit)).all()
    return facade.ProgramPage(items=facade.hydrate_programs(db,keys,legacy),total=total,
        next_offset=offset+limit if offset+limit<total else None,years=years,subjects=[])


def archive_union(query,legacy):
    parts=[select(literal(p.id).label('id'),literal(p.program_id).label('pid'),literal(None).label('rid'),
        literal(p.university_id).label('university_id'),literal(p.year).label('year'),
        literal(p.title.casefold()).label('sort_text'),
        literal(f'{p.title} {p.code or ""} {p.university_name}'.casefold()).label('search_text')) for p in legacy.values()]
    return union_all(query,*parts).subquery() if parts else query.subquery()


def create_prototype(engine,name,query):
    sql=str(query.compile(dialect=engine.dialect,compile_kwargs={'literal_binds':True}))
    with engine.begin() as db:
        db.exec_driver_sql(f'CREATE TABLE {name} AS '+sql)
        for suffix,columns in [('public','id,rid,pid'),('scope','pid,cid,rid'),
                ('order','sort_text,id'),('year','year,sort_text,id'),('university','university_id,year,sort_text,id')]:
            if suffix=='scope' and name=='scale_eligible':
                continue
            db.exec_driver_sql(f'CREATE INDEX {name}_{suffix} ON {name} ({columns})')
        db.exec_driver_sql(f'ANALYZE {name}')
    return Table(name,MetaData(),autoload_with=engine)


def prepared_factory(table,*,check_conflicts):
    known=[r.id for r in load_catalog().institutions]+[r.id for r in load_registry().registry_only]
    def index(db):
        legacy={p.id:p for p in facade.legacy_programs(db)}
        fields=['id','pid','rid','university_id','year','sort_text','search_text']
        query=select(*(table.c[k] for k in fields))
        if check_conflicts:
            query=query.where(table.c.university_id.in_(known))
            rival=table.alias('rival_public')
            other=table.alias('rival_scope')
            query=query.where(~exists(select(1).select_from(rival).where(rival.c.id==table.c.id,
                rival.c.university_id.in_(known),(rival.c.rid!=table.c.rid)|(rival.c.pid!=table.c.pid))).correlate(table),
                ~exists(select(1).select_from(other).where(other.c.pid==table.c.pid,other.c.cid==table.c.cid,
                    other.c.university_id.in_(known),other.c.rid!=table.c.rid)).correlate(table))
        query=query.where(table.c.id.not_in(facade.REVIEWED_IDS))
        return archive_union(query,legacy),legacy
    return index


def pg_stats(engine):
    with engine.connect() as db:
        db.execute(text('SELECT pg_stat_clear_snapshot()'))
        return dict(db.execute(text('SELECT temp_bytes,temp_files,blks_read,blks_hit,xact_commit,tup_returned FROM pg_stat_database WHERE datname=current_database()')).mappings().one())


class Resources:
    def __init__(self,name):
        self.name=name;self.stop=threading.Event();self.samples=[]
    def run(self):
        while not self.stop.is_set():
            start=time.monotonic()
            try:
                result=subprocess.run(['docker','stats','--no-stream','--format','{{json .}}',self.name],
                    capture_output=True,text=True,timeout=5,check=True)
                self.samples.append(dict(seconds=time.monotonic()-start,**json.loads(result.stdout)))
            except (subprocess.SubprocessError,json.JSONDecodeError) as error:
                self.samples.append({'error':type(error).__name__})
            self.stop.wait(.25)


def load_test(client,params,workers,engine,runtime,seconds):
    barrier=threading.Barrier(workers)
    before=pg_stats(engine)
    monitor=Resources(runtime.name)
    thread=threading.Thread(target=monitor.run,daemon=True);thread.start()
    def worker(_):
        barrier.wait(timeout=30)
        rows=[]
        deadline=time.monotonic()+seconds
        while len(rows)<max(2,math.ceil(50/workers)) or time.monotonic()<deadline:
            start=time.perf_counter()
            response=client.get('/api/v1/catalog/programs',params=params)
            rows.append(dict(ms=(time.perf_counter()-start)*1000,status=response.status_code,
                total=response.json().get('total') if response.status_code==200 else None))
        return rows
    start=time.perf_counter()
    try:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            rows=[r for batch in pool.map(worker,range(workers)) for r in batch]
    finally:
        monitor.stop.set();thread.join(timeout=6)
    elapsed=time.perf_counter()-start
    after=pg_stats(engine)
    values=sorted(r['ms'] for r in rows)
    return dict(concurrency=workers,requests=len(rows),seconds=elapsed,rps=len(rows)/elapsed,
        p50=statistics.median(values),p95=values[math.ceil(.95*len(values))-1],
        failures=sum(r['status']!=200 for r in rows),totals=sorted({r['total'] for r in rows if r['total'] is not None}),
        samples=rows,postgresStatsDelta={k:after[k]-before[k] for k in before},
        postgresContainerSamples=monitor.samples,
        resourcePolicy='Docker working-set/CPU of the owned PostgreSQL container; includes background PG activity, excludes Python. pg_stat_database counters may lag by one statistics flush interval.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--variants',nargs='+',default=['transactional','prepared-current','prepared-eligible','sql','source-indexed'])
    parser.add_argument('--shm-size',choices=['64m','1g'],default='1g')
    parser.add_argument('--load-seconds',type=int,default=10)
    parser.add_argument('--direct',action='store_true',help='Indexable separate exact queries for prepared variants')
    args=parser.parse_args()
    if not set(args.variants)<={'sql','source-indexed','transactional','prepared-current','prepared-eligible'}:
        parser.error('unknown variant')
    if not args.direct and any(v.startswith('prepared-') for v in args.variants):
        parser.error('frozen prepared prototypes require --direct; historical consolidated trials are preserved separately')
    report=dict(experimental=True,sourceCommit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True)),
        shmSize=args.shm_size,loadSeconds=args.load_seconds,direct=args.direct,variants={})
    def save():
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    original=facade.program_index
    original_page=facade.program_page
    source_index=facade.source_program_index
    source_page=facade.source_program_page
    try:
        with disposable_postgres(shm_size=args.shm_size) as runtime,isolated_postgres(runtime.url()) as engine:
            upgrade_schema(engine);import_reviewed(engine)
            print('Seeding100k...',flush=True)
            start=time.perf_counter()
            report['fixture']=seed(engine,target_year_per_campaign=100)
            report['seedWithPublicationSeconds']=time.perf_counter()-start
            with engine.connect() as db:
                report['postgresVersion']=db.scalar(text('SHOW server_version'))
                report['schemaRevision']=db.scalar(text('SELECT version_num FROM alembic_version'))
                report['settings']={key:db.scalar(text('SELECT current_setting(:key)'),{'key':key}) for key in
                    ['work_mem','hash_mem_multiplier','shared_buffers','max_parallel_workers_per_gather','max_connections','dynamic_shared_memory_type','track_io_timing']}
            with Session(engine) as db:
                index,_=source_index(db)
                eligible_query=select(index).where(index.c.rid.is_not(None))
                eligible=create_prototype(engine,'scale_eligible',eligible_query)
            current_query=(select(Fact.public_id.label('id'),Fact.program_id.label('pid'),Fact.revision_id.label('rid'),
                Fact.campaign_id.label('cid'),Campaign.university_id,Campaign.year,Fact.sort_text,Fact.search_text)
                .join(Revision,Revision.id==Fact.revision_id).join(Publication,Publication.revision_id==Revision.id)
                .join(Campaign,Campaign.id==Fact.campaign_id).where(Revision.verification_status=='verified'))
            current=create_prototype(engine,'scale_current',current_query)
            # Visibility-map state is recorded; steady-state and subsequent
            # transactional-update benchmarks must be reported separately.
            with engine.connect().execution_options(isolation_level='AUTOCOMMIT') as db:
                db.exec_driver_sql('VACUUM ANALYZE scale_current');db.exec_driver_sql('VACUUM ANALYZE scale_eligible')
            cases=dict(first={},university={'university_id':report['fixture']['sampleUniversity'],'year':2027},
                code={'q':'09.03.04','year':2027},deep={'year':2027,'offset':99988})
            oracle={}
            for name,params in cases.items():
                with Session(engine) as db:
                    result=source_page(db,**params)
                    oracle[name]=hashlib.sha256(json.dumps(result.model_dump(mode='json'),ensure_ascii=False,sort_keys=True).encode()).hexdigest()
            report['oracle']=oracle
            for variant in args.variants:
                if variant=='source-indexed':
                    start=time.perf_counter()
                    with engine.begin() as db:
                        db.exec_driver_sql('CREATE INDEX scale_source_scope ON program_catalog_facts(program_id,campaign_id,revision_id)')
                        db.exec_driver_sql('CREATE INDEX scale_source_campaign_order ON program_catalog_facts(campaign_id,sort_text,public_id)')
                        db.exec_driver_sql('CREATE INDEX scale_source_publication ON program_catalog_publications(revision_id)')
                        db.exec_driver_sql('CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public')
                        db.exec_driver_sql('CREATE INDEX scale_source_search ON program_catalog_facts USING gin(search_text public.gin_trgm_ops)')
                        db.exec_driver_sql('ANALYZE')
                        report['sourceIndexBytes']=db.scalar(text("SELECT sum(pg_relation_size(indexrelid)) FROM pg_index WHERE indexrelid::regclass::text LIKE '%scale_source_%'"))
                    report['sourceIndexBuildSeconds']=time.perf_counter()-start
                if variant in ('sql','source-indexed'):
                    facade.program_index=source_index;facade.program_page=source_page
                elif variant=='transactional':
                    facade.program_index=original;facade.program_page=original_page
                else:
                    facade.program_index=prepared_factory(current if variant=='prepared-current' else eligible,check_conflicts=variant=='prepared-current')
                    facade.program_page=direct_page
                benchmark.program_page=facade.program_page
                report['variants'][variant]={}
                url=engine.url.update_query_dict({'options':engine.url.query['options']+' -cstatement_timeout=10000'})
                app=create_app(Settings(database_url=url.render_as_string(hide_password=False),auto_create_schema=False))
                with TestClient(app,raise_server_exceptions=False) as client:
                    for name,params in cases.items():
                        print(variant+' '+name,flush=True)
                        for _ in range(10):
                            with Session(engine) as db:facade.program_page(db,**params)
                        monitor=Resources(runtime.name);thread=threading.Thread(target=monitor.run,daemon=True)
                        before=pg_stats(engine);thread.start()
                        try:result=measure(engine,params,50,10000)
                        finally:monitor.stop.set();thread.join(timeout=6)
                        after=pg_stats(engine)
                        result['matchesSourceOracle']=result.get('responseSha256')==oracle[name]
                        result['singlePostgresStatsDelta']={k:after[k]-before[k] for k in before}
                        result['singlePostgresContainerSamples']=monitor.samples
                        http_params={('universityId' if k=='university_id' else k):v for k,v in params.items()}
                        for _ in range(10):client.get('/api/v1/catalog/programs',params=http_params)
                        result['httpSingle']=load_test(client,http_params,1,engine,runtime,args.load_seconds)
                        result['concurrent']=[load_test(client,http_params,n,engine,runtime,args.load_seconds) for n in (10,25,50)]
                        report['variants'][variant][name]=result;save()
    finally:
        facade.program_index=original
        facade.program_page=original_page
        benchmark.program_page=original_page
    save()


if __name__=='__main__':main()
