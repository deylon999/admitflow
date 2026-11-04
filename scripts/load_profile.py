#!/usr/bin/env python3
"""T044: QUALITY Q12 profile over real HTTP and PostgreSQL. Synthetic rows only, no external fetch."""
import argparse
import asyncio
from datetime import datetime, timedelta, timezone
import json
import math
import os
from pathlib import Path
import platform
import random
import secrets
import subprocess
import sys
import tempfile
import threading
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'scripts')]
os.environ.setdefault('SOURCE_IDENTITY_KEY',secrets.token_hex(32))
import httpx
from sqlalchemy.orm import Session
from app.admissions import Campaign, CompetitionGroup, Source, University
from app.database import make_engine
from app.migrations import upgrade_schema
from app.sources.contracts import SourceBinding
from app.sources.publishing import publish
from app.sources.storage import RawStore
from load_support import URL, VERSION, load_registry, raw_for, rows_list

HEADERS={'X-Requested-With':'abiturient'}
BINDING=SourceBinding('load-source','load-group',2026,URL,'example.org',VERSION,'live',True)
MANUAL=dict(university='Load stand',title='Synthetic group',sourceUrl='https://example.org/list',values=dict(rank=120,seats=90,excluded=30,noConsent=16))


def percentile(values,share):
    ordered=sorted(values)
    return round(ordered[max(0,math.ceil(share*len(ordered))-1)],2) if ordered else None


def summary(samples):
    times=[elapsed for elapsed,_ in samples]
    statuses={}
    for _,status in samples:
        statuses[str(status)]=statuses.get(str(status),0)+1
    return dict(requests=len(samples),p50Ms=percentile(times,.5),p95Ms=percentile(times,.95),p99Ms=percentile(times,.99),maxMs=round(max(times),2) if times else None,
                statuses=statuses,unexpected5xxShare=round(sum(status>=500 for _,status in samples)/max(1,len(samples)),4))


def seed(engine,seats):
    now=datetime(2026,11,1,tzinfo=timezone.utc)
    with Session(engine) as db:
        db.add(University(id='load-u',name='Synthetic load stand',official_url='https://example.org',provenance_url=URL,verified_at=now));db.flush()
        db.add(Campaign(id='load-c',university_id='load-u',year=2026,level='bachelor'));db.flush()
        db.add(CompetitionGroup(id='load-group',campaign_id='load-c',official_id='load',title='Synthetic load group',study_form='full-time',funding='budget',category='general',seats=seats,coverage='candidate',rules_version='listed-consent-v1'));db.flush()
        db.add(Source(id='load-source',group_id='load-group',url=URL,domain='example.org',adapter_version=VERSION,snapshot_kind='live',enabled=True))
        db.commit()


ROUTES={}


async def timed(samples,call,route=None):
    begin=time.perf_counter()
    try:
        response=await call
        status=response.status_code
    except httpx.HTTPError:
        response,status=None,599
    samples.append(((time.perf_counter()-begin)*1000,status))
    if route:
        ROUTES.setdefault(route,[]).append(samples[-1])
    return response


async def prepare_session(index,base,samples,directions,offset):
    client=httpx.AsyncClient(base_url=base,headers=HEADERS,timeout=60,trust_env=False)
    await timed(samples,client.post('/api/v1/session'))
    ids=[]
    for number in range(directions//2):
        code=f'LOAD-{offset+index*directions+number+1:06}'
        found=await timed(samples,client.post('/api/v1/sources/load-source/lookup',json={'publicCode':code}))
        if found is None or found.status_code!=200:
            continue
        saved=await timed(samples,client.post('/api/v1/subscriptions',json={'confirmationToken':found.json()['confirmationToken']}))
        if saved is not None and saved.status_code==201:
            ids.append(saved.json()['id'])
    for number in range(directions-directions//2):
        await timed(samples,client.post('/api/v1/watches',json=MANUAL,headers={'Idempotency-Key':f'load-{index}-{number}'}))
    return client,ids


async def reader(client,ids,samples,stop,pace):
    position=random.randrange(6)
    # Sessions start apart: 100 identical simultaneous first requests are not a real profile.
    await asyncio.sleep(random.uniform(0,pace))
    while not stop.is_set():
        route=position%6
        path=['/api/v1/subscriptions','/api/v1/watches','/api/v1/direction-budget',f'/api/v1/subscriptions/{ids[position%len(ids)]}/scenario','/api/v1/groups','/api/v1/sources/load-source/status'][route] if ids else '/api/v1/watches'
        await timed(samples,client.get(path),['subscriptions','watches','budget','scenario','groups','status'][route])
        position+=1
        await asyncio.sleep(pace)


async def drive(args,base,engine,store,registry):
    prepare=[]
    semaphore=asyncio.Semaphore(args.prepare_concurrency)
    async def one(index):
        async with semaphore:
            return await prepare_session(index,base,prepare,args.directions,0)
    begin=time.perf_counter()
    clients=await asyncio.gather(*(one(index) for index in range(args.sessions)))
    report=dict(prepare=summary(prepare)|dict(seconds=round(time.perf_counter()-begin,1)),subscriptions=sum(len(ids) for _,ids in clients))
    stop=asyncio.Event()
    idle=[]
    tasks=[asyncio.create_task(reader(client,ids,idle,stop,args.pace)) for client,ids in clients]
    await asyncio.sleep(args.seconds)
    stop.set()
    await asyncio.gather(*tasks)
    report['readsWithoutPublication']=summary(idle)
    report['routesWithoutPublication']={name:summary(values) for name,values in sorted(ROUTES.items())}
    stop=asyncio.Event()
    during=[]
    tasks=[asyncio.create_task(reader(client,ids,during,stop,args.pace)) for client,ids in clients]
    published=dict()
    def republish():
        begin=time.perf_counter()
        at=datetime.now(timezone.utc)
        publish(engine,BINDING.source_id,rows_list(BINDING,args.rows,args.seats,1),raw_for(1,at),store,registry=registry)
        published['seconds']=round(time.perf_counter()-begin,2)
    worker=threading.Thread(target=republish)
    worker.start()
    while worker.is_alive():
        await asyncio.sleep(.5)
    await asyncio.sleep(5)
    stop.set()
    await asyncio.gather(*tasks)
    worker.join()
    report['readsDuringPublication']=summary(during)
    report['publicationWithSubscriptionsSeconds']=published.get('seconds')
    await asyncio.gather(*(client.aclose() for client,_ in clients))
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database-url',required=True,help='Disposable admitflow_test* PostgreSQL database')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--sessions',type=int,default=100)
    parser.add_argument('--directions',type=int,default=20)
    parser.add_argument('--rows',type=int,default=10000)
    parser.add_argument('--seats',type=int,default=1000)
    parser.add_argument('--seconds',type=int,default=60)
    parser.add_argument('--prepare-concurrency',type=int,default=10)
    parser.add_argument('--port',type=int,default=8123)
    parser.add_argument('--pace',type=float,default=5,help='Seconds between requests of one session')
    parser.add_argument('--api-workers',type=int,default=1)
    args=parser.parse_args()
    if 'admitflow_test' not in args.database_url:
        parser.error('refusing a database that is not disposable')
    engine=make_engine(args.database_url)
    upgrade_schema(engine)
    seed(engine,args.seats)
    registry=load_registry()
    with tempfile.TemporaryDirectory(prefix='admitflow-load-') as folder:
        store=RawStore(Path(folder)/'raw')
        begin=time.perf_counter()
        at=datetime.now(timezone.utc)-timedelta(minutes=5)
        publish(engine,BINDING.source_id,rows_list(BINDING,args.rows,args.seats),raw_for(0,at),store,registry=registry)
        first=round(time.perf_counter()-begin,2)
        env={**os.environ,'DATABASE_URL':args.database_url,'AUTO_CREATE_SCHEMA':'false','LOAD_PORT':str(args.port),'RAW_STORE_PATH':str(store.root),'LOAD_WORKERS':str(args.api_workers)}
        server=subprocess.Popen([sys.executable,str(ROOT/'scripts/load_server.py')],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        base=f'http://127.0.0.1:{args.port}'
        try:
            for _ in range(60):
                try:
                    if httpx.get(base+'/api/health',trust_env=False).status_code==200:
                        break
                except httpx.HTTPError:
                    pass
                time.sleep(1)
            report=asyncio.run(drive(args,base,engine,store,registry))
            rss=next(line for line in Path(f'/proc/{server.pid}/status').read_text().splitlines() if line.startswith('VmHWM'))
        finally:
            server.terminate()
            server.wait(10)
    engine.dispose()
    target=report['readsWithoutPublication']['p95Ms']<500 and report['readsDuringPublication']['p95Ms']<500 and report['readsWithoutPublication']['unexpected5xxShare']<.01 and report['readsDuringPublication']['unexpected5xxShare']<.01
    report=dict(recordedAt=datetime.now(timezone.utc).isoformat(),stand=dict(name=os.getenv('LOAD_STAND','unnamed'),python=platform.python_version(),cpuCount=os.cpu_count(),apiProcesses=args.api_workers,database='PostgreSQL',tls=False,clientOnSameHost=True),
                profile=dict(sessions=args.sessions,directionsPerSession=args.directions,rows=args.rows,seats=args.seats,readSeconds=args.seconds,pacePerSessionSeconds=args.pace,externalFetches=0),
                firstPublicationSeconds=first,**report,apiPeakRss=rss.split(':')[1].strip(),targetMet=target,
                scope='Synthetic rows on the named stand. QUALITY target for staging is measured separately after deployment.')
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))
    return 0 if target else 1


if __name__=='__main__':
    raise SystemExit(main())
