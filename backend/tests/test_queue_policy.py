from datetime import timedelta
from sqlalchemy.orm import Session
from app.jobs import SourceJob,claim,enqueue,fail
from source_helpers import NOW,seed_source


def test_explicit_policy_changes_apply_only_to_eligible_reenqueue(source_engine):
    seed_source(source_engine)
    assert enqueue(source_engine,'source-1',now=NOW,interval_seconds=60,max_attempts=1)
    lease=claim(source_engine,now=NOW)
    assert not enqueue(source_engine,'source-1',now=NOW,interval_seconds=120,max_attempts=3)
    fail(source_engine,lease,'network_error',now=NOW)
    assert not enqueue(source_engine,'source-1',now=NOW+timedelta(seconds=59),interval_seconds=120,max_attempts=3)
    with Session(source_engine) as db:
        job=db.get(SourceJob,'source-1')
        assert job.interval_seconds==60 and job.max_attempts==1
    assert enqueue(source_engine,'source-1',now=NOW+timedelta(seconds=61),interval_seconds=120,max_attempts=3)
    with Session(source_engine) as db:
        job=db.get(SourceJob,'source-1')
        assert (job.interval_seconds,job.max_attempts,job.attempts,job.state)==(120,3,0,'queued')
