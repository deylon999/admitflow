"""Synthetic scale only: no real sources, network or coverage attestation."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import json
import os
from pathlib import Path
import time

import pytest
from sqlalchemy import insert,select,func,update
from sqlalchemy.orm import Session

from app.admissions import Source
from app.jobs import SourceJob,SourceCheck,LostLease,claim,complete,enqueue,renew
from native_support import postgres_engine
from source_helpers import NOW,seed_source

pytestmark=pytest.mark.postgres


def test_one_thousand_sources_keep_domain_leases_fencing_and_unique_jobs(postgres_engine):
    started=time.perf_counter();seed_source(postgres_engine)
    sources=[dict(id=f'scale-{i:04d}',group_id='group-1',url=f'https://host-{i%100:03d}.fixtures.invalid/{i}',
        domain=f'host-{i%100:03d}.fixtures.invalid',adapter_version='synthetic-v1',snapshot_kind='archive',enabled=True)
        for i in range(1000)]
    # Bulk preparation tests the scheduler, not repeated seed/HTTP overhead.
    with Session(postgres_engine) as db:
        db.execute(insert(Source),sources)
        db.execute(insert(SourceJob),[dict(source_id=s['id'],state='queued',next_run_at=NOW,attempts=0,max_attempts=5,interval_seconds=900) for s in sources[:-1]])
        db.commit()
    with ThreadPoolExecutor(max_workers=12) as pool:
        queued=list(pool.map(lambda _:enqueue(postgres_engine,sources[-1]['id'],now=NOW),range(24)))
    assert sum(queued)==1

    def occupy(at):
        found=[]
        with ThreadPoolExecutor(max_workers=12) as pool:
            batch=list(pool.map(lambda _:claim(postgres_engine,now=at,lease_seconds=30),range(100)))
            found.extend(lease for lease in batch if lease)
        # SKIP LOCKED is allowed to return idle while another transaction owns
        # a candidate batch; after the parallel wave all those locks are gone.
        while len(found)<100:
            lease=claim(postgres_engine,now=at,lease_seconds=30)
            assert lease is not None
            found.append(lease)
        assert len(found)==100
        assert len({lease.source_id for lease in found})==100
        with Session(postgres_engine) as db:
            running=db.execute(select(Source.domain,func.count()).join(SourceJob,SourceJob.source_id==Source.id)
                .where(SourceJob.state=='running',SourceJob.lease_until>at).group_by(Source.domain)).all()
        assert len(running)==100 and all(count==1 for _,count in running)
        assert claim(postgres_engine,now=at) is None
        return found

    old=occupy(NOW);recovered_at=NOW+timedelta(seconds=31)
    # Make only the expired owners due for this recovery wave. Otherwise the
    # scheduler may correctly choose a different queued scope on the same host.
    with Session(postgres_engine) as db:
        db.execute(update(SourceJob).where(SourceJob.state=='queued').values(next_run_at=NOW+timedelta(days=1)))
        db.commit()
    recovered=occupy(recovered_at)
    assert {lease.source_id for lease in recovered}=={lease.source_id for lease in old}
    for previous in old:
        with pytest.raises(LostLease):renew(postgres_engine,previous,now=recovered_at)
        with pytest.raises(LostLease):complete(postgres_engine,previous,now=recovered_at)
    with Session(postgres_engine) as db:
        db.execute(update(SourceJob).where(SourceJob.state=='queued').values(next_run_at=NOW))
        db.commit()
    seen=set()
    with ThreadPoolExecutor(max_workers=12) as pool:
        for wave in range(10):
            leases=recovered if wave==0 else occupy(recovered_at)
            ids={lease.source_id for lease in leases}
            assert not ids&seen;seen.update(ids)
            list(pool.map(lambda lease:complete(postgres_engine,lease,now=recovered_at),leases))
    assert len(seen)==1000 and claim(postgres_engine,now=recovered_at) is None
    with Session(postgres_engine) as db:
        assert db.scalar(select(func.count()).select_from(SourceJob))==1000
        assert db.scalar(select(func.count()).select_from(SourceCheck))==1000
        assert db.scalar(select(func.count()).select_from(SourceJob).where(SourceJob.state=='idle',SourceJob.attempts==0))==1000
    # Optional aggregate artifact used by the owned native verification runner.
    report=dict(synthetic=True,realCoverageAdded=0,sourceCount=1000,domains=100,claimThreads=12,
        simultaneousDomains=100,maxActivePerDomain=1,recoveredLeases=100,rejectedOldRenewals=100,
        rejectedOldCompletions=100,successfulUniqueCompletions=1000,concurrentEnqueueCalls=24,
        insertedEnqueueJobs=1,duplicateCompletions=0,seconds=round(time.perf_counter()-started,3))
    if output:=os.getenv('MASS_QUEUE_REPORT'):
        Path(output).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
