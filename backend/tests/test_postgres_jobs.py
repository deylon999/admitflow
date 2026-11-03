"""Native row-lock/lease checks; fixtures are synthetic and never attested."""
from concurrent.futures import ThreadPoolExecutor
import multiprocessing

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import make_engine
from app.jobs import SourceJob, claim, enqueue
from native_support import postgres_engine
from source_helpers import NOW, seed_source
from test_jobs import (
    test_one_source_one_active_claim_and_periodic_schedule,
    test_lease_recovery_rejects_old_owner_and_exhausts_attempts,
    test_retry_after_is_respected_and_disabled_source_cancels_owner,
    test_retry_limit_and_permanent_failure_do_not_spin,
)
from test_worker import (
    test_worker_lost_lease_cannot_publish,
    test_disable_during_fetch_prevents_publication,
)
from test_domain_queue import (
    test_same_domain_is_serialized_but_other_domains_are_not,
    test_progress_heartbeat_cannot_revive_expired_or_disabled_owner,
    test_different_domains_can_run_at_once,
)

pytestmark = pytest.mark.postgres


@pytest.fixture
def source_engine(postgres_engine):
    return postgres_engine


def claim_in_process(url, ready, gate, results):
    engine = make_engine(url)
    try:
        ready.put(True)
        if not gate.wait(timeout=15):
            raise RuntimeError('Worker start gate timed out')
        lease = claim(engine, now=NOW)
        results.put(lease.source_id if lease else None)
    finally:
        engine.dispose()


def test_independent_processes_claim_one_source_once(source_engine):
    seed_source(source_engine)
    assert enqueue(source_engine, 'source-1', now=NOW)
    context = multiprocessing.get_context('spawn')
    ready, results, gate = context.Queue(), context.Queue(), context.Event()
    processes = [context.Process(target=claim_in_process, args=(
        source_engine.url.render_as_string(hide_password=False), ready, gate, results,
    )) for _ in range(2)]
    try:
        for process in processes:
            process.start()
        for _ in processes:
            assert ready.get(timeout=15) is True
        gate.set()
        claimed = [results.get(timeout=15) for _ in processes]
        assert claimed.count('source-1') == 1 and claimed.count(None) == 1
        for process in processes:
            process.join(timeout=10)
            assert process.exitcode == 0
        with Session(source_engine) as db:
            job = db.get(SourceJob, 'source-1')
            assert job.state == 'running' and job.attempts == 1
    finally:
        gate.set()
        for process in processes:
            if process.pid is not None:
                if process.is_alive():
                    process.terminate()
                process.join(timeout=5)
        ready.close()
        results.close()


def test_claim_skips_a_locked_job_without_waiting(source_engine):
    seed_source(source_engine)
    enqueue(source_engine, 'source-1', now=NOW)
    # A second connection must finish while this transaction still owns the lock.
    with ThreadPoolExecutor(max_workers=1) as pool:
        with Session(source_engine) as db:
            db.scalar(select(SourceJob).with_for_update())
            assert pool.submit(claim, source_engine, now=NOW).result(timeout=2) is None
    assert claim(source_engine, now=NOW).source_id == 'source-1'
