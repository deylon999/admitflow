#!/usr/bin/env python3
"""Measure a named local ASGI/PostgreSQL profile using anonymized source facts."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import json
import math
import os
from pathlib import Path
import platform
import resource
import sys
import tempfile
from threading import Lock
import time
from postgres_runtime import disposable_postgres
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/tests')]
from fastapi.testclient import TestClient
from sqlalchemy import event
from app.config import Settings
from app.database import make_engine
from app.main import create_app
from app.migrations import upgrade_schema
from app.sources.pilots import register_sgu
from app.sources.publishing import publish
from app.sources.storage import RawStore
from test_api import HEADERS,start
from test_sgu_adapter import BINDING,KEY,response


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    os.environ['SOURCE_IDENTITY_KEY']=KEY.hex()
    with tempfile.TemporaryDirectory(prefix='admitflow-archive-load-') as folder,disposable_postgres() as runtime:
        engine=make_engine(runtime.url());upgrade_schema(engine);engine.dispose()
        app=create_app(Settings(database_url=runtime.url(),auto_create_schema=False))
        with TestClient(app) as client:
            register_sgu(app.state.engine,enable=True,registry=app.state.source_registry)
            raw=response();adapter=app.state.source_registry.resolve(BINDING)
            publish(app.state.engine,BINDING.source_id,adapter.parse(raw,BINDING),raw,RawStore(Path(folder)/'raw'),registry=app.state.source_registry)
            start(client);ids=[]
            for i in range(1,21):
                lookup=client.post(f'/api/v1/sources/{BINDING.source_id}/lookup',json={'publicCode':f'FIXTURE-{i:06}'},headers=HEADERS)
                assert lookup.status_code==200
                saved=client.post('/api/v1/subscriptions',json={'confirmationToken':lookup.json()['confirmationToken']},headers=HEADERS)
                assert saved.status_code==201;ids.append(saved.json()['id'])
            assert client.get('/api/v1/direction-budget').json()['total']==20
            client.get('/api/v1/subscriptions').raise_for_status()  # Warm connection pools only.
            sql=[0];lock=Lock()
            def count(*_):
                with lock:sql[0]+=1
            event.listen(app.state.engine,'before_cursor_execute',count)
            def read(index):
                path='/api/v1/subscriptions' if index<60 else f'/api/v1/subscriptions/{ids[index%20]}/history'
                begin=time.perf_counter();result=client.get(path);elapsed=(time.perf_counter()-begin)*1000
                if result.status_code==200:
                    value=result.json();assert len(value)==20 if index<60 else value['total']==1
                return elapsed,result.status_code
            begin=time.perf_counter()
            with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(read,range(80)))
            duration=time.perf_counter()-begin
            event.remove(app.state.engine,'before_cursor_execute',count)
            samples=sorted(value for value,_ in results);statuses={str(status):sum(s==status for _,s in results) for _,status in results}
            report=dict(recordedAt=datetime.now(timezone.utc).isoformat(),profile={'rows':573,'subscriptions':20,'concurrentReaders':4,'listRequests':60,'historyRequests':20,'externalFetches':0,'transport':'FastAPI TestClient/ASGI + native disposable PostgreSQL17,no nginx/TLS'},
                        host={'python':platform.python_version(),'system':platform.system(),'cpuCount':os.cpu_count()},
                        durationSeconds=round(duration,3),p50Ms=round(samples[math.ceil(.5*len(samples))-1],2),p95Ms=round(samples[math.ceil(.95*len(samples))-1],2),maxMs=round(max(samples),2),
                        statuses=statuses,sqlStatements=sql[0],meanSqlPerRead=round(sql[0]/80,2),processPeakRssMiB=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,2),
                        localTargetP95Ms=500,localTargetMet=samples[math.ceil(.95*len(samples))-1]<500,unexpected5xx=sum(s>=500 for _,s in results),
                        scope='one anonymized archive group;no simultaneous publication or source fetch;not T044 broad staging/load/soak gate')
    report['cleanup']=True;args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
    return 0 if not report['unexpected5xx'] and report['localTargetMet'] else 1


if __name__=='__main__':raise SystemExit(main())
