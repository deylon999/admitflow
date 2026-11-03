from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest
from sqlalchemy.orm import Session

from app.admissions import Source
from app.jobs import LostLease,SourceJob,claim,complete,disable,enqueue,renew
from source_helpers import NOW,seed_source


def seed_second(engine,domain='example.org'):
    with Session(engine) as db:
        db.add(Source(id='source-2',group_id='group-1',url=f'https://{domain}/another',domain=domain,adapter_version='synthetic-v1',snapshot_kind='archive',enabled=True));db.commit()


def test_same_domain_is_serialized_but_other_domains_are_not(source_engine):
    seed_source(source_engine);seed_second(source_engine)
    enqueue(source_engine,'source-1',now=NOW);enqueue(source_engine,'source-2',now=NOW)
    with ThreadPoolExecutor(max_workers=2) as pool:leases=list(pool.map(lambda _:claim(source_engine,now=NOW),range(2)))
    assert sum(lease is not None for lease in leases)==1
    winner=next(lease for lease in leases if lease)
    complete(source_engine,winner,now=NOW)
    second=claim(source_engine,now=NOW)
    assert second and second.source_id!=winner.source_id


def test_progress_heartbeat_cannot_revive_expired_or_disabled_owner(source_engine):
    seed_source(source_engine);enqueue(source_engine,'source-1',now=NOW)
    first=claim(source_engine,now=NOW,lease_seconds=30)
    renew(source_engine,first,now=NOW+timedelta(seconds=20),lease_seconds=60)
    assert claim(source_engine,now=NOW+timedelta(seconds=31)) is None
    with pytest.raises(LostLease):renew(source_engine,first,now=NOW+timedelta(seconds=81))
    second=claim(source_engine,now=NOW+timedelta(seconds=81))
    with pytest.raises(LostLease):renew(source_engine,first,now=NOW+timedelta(seconds=82))
    disable(source_engine,'source-1',now=NOW+timedelta(seconds=82))
    with pytest.raises(LostLease):renew(source_engine,second,now=NOW+timedelta(seconds=83))


def test_different_domains_can_run_at_once(source_engine):
    seed_source(source_engine);seed_second(source_engine,'other.example.org')
    enqueue(source_engine,'source-1',now=NOW);enqueue(source_engine,'source-2',now=NOW)
    assert claim(source_engine,now=NOW) is not None
    assert claim(source_engine,now=NOW) is not None
