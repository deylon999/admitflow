from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest
from sqlalchemy.orm import Session

from app.admissions import Source
from app.jobs import LostLease, SourceJob, claim, complete, disable, enqueue, fail, guard_lease
from source_helpers import NOW, seed_source


def test_one_source_one_active_claim_and_periodic_schedule(source_engine):
    seed_source(source_engine)
    with ThreadPoolExecutor(max_workers=8) as pool:
        results=list(pool.map(lambda _:enqueue(source_engine,'source-1',now=NOW,interval_seconds=60),range(16)))
    assert sum(results)==1
    with ThreadPoolExecutor(max_workers=8) as pool:
        leases=list(pool.map(lambda _:claim(source_engine,now=NOW),range(16)))
    leases=[lease for lease in leases if lease]
    assert len(leases)==1
    assert not enqueue(source_engine,'source-1',now=NOW)
    complete(source_engine,leases[0],now=NOW)
    assert claim(source_engine,now=NOW+timedelta(seconds=59)) is None
    assert not enqueue(source_engine,'source-1',now=NOW+timedelta(seconds=59))
    assert claim(source_engine,now=NOW+timedelta(seconds=60)).attempt==1


def test_lease_recovery_rejects_old_owner_and_exhausts_attempts(source_engine):
    seed_source(source_engine)
    enqueue(source_engine,'source-1',now=NOW,max_attempts=2)
    first=claim(source_engine,now=NOW,lease_seconds=30)
    second=claim(source_engine,now=NOW+timedelta(seconds=31),lease_seconds=30)
    assert second.token!=first.token and second.attempt==2
    with pytest.raises(LostLease):
        complete(source_engine,first,now=NOW+timedelta(seconds=32))
    with Session(source_engine) as db:
        with pytest.raises(LostLease):
            guard_lease(db,first,now=NOW+timedelta(seconds=32))
    assert claim(source_engine,now=NOW+timedelta(seconds=62)) is None
    with Session(source_engine) as db:
        assert db.get(SourceJob,'source-1').state=='failed'


def test_retry_after_is_respected_and_disabled_source_cancels_owner(source_engine):
    seed_source(source_engine)
    enqueue(source_engine,'source-1',now=NOW,interval_seconds=60)
    lease=claim(source_engine,now=NOW)
    fail(source_engine,lease,'rate_limited',retry_after=300,now=NOW)
    assert claim(source_engine,now=NOW+timedelta(seconds=299)) is None
    assert not enqueue(source_engine,'source-1',now=NOW+timedelta(seconds=299))
    retry=claim(source_engine,now=NOW+timedelta(seconds=300))
    assert retry.attempt==2
    disable(source_engine,'source-1',now=NOW+timedelta(seconds=301))
    with pytest.raises(LostLease):
        fail(source_engine,retry,'network_error',now=NOW+timedelta(seconds=302))
    assert claim(source_engine,now=NOW+timedelta(days=1)) is None
    with Session(source_engine) as db:
        assert not db.get(Source,'source-1').enabled
        assert db.get(SourceJob,'source-1').token is None


def test_retry_limit_and_permanent_failure_do_not_spin(source_engine):
    seed_source(source_engine)
    enqueue(source_engine,'source-1',now=NOW,interval_seconds=60,max_attempts=2)
    first=claim(source_engine,now=NOW)
    fail(source_engine,first,'network_error',retry_after=60,now=NOW)
    second=claim(source_engine,now=NOW+timedelta(minutes=1))
    fail(source_engine,second,'network_error',retry_after=60,now=NOW+timedelta(minutes=1))
    assert claim(source_engine,now=NOW+timedelta(days=1)) is None
    assert enqueue(source_engine,'source-1',now=NOW+timedelta(days=1))
    third=claim(source_engine,now=NOW+timedelta(days=1))
    fail(source_engine,third,'invalid_format',now=NOW+timedelta(days=1))
    assert claim(source_engine,now=NOW+timedelta(days=2)) is None
