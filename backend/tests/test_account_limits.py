from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from threading import Barrier

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.account_limits import AuthRateExceeded, Budget, consume_budgets
from app.accounts import AccountRateBucket
from app.database import make_engine
from native_support import postgres_engine  # noqa: F401

pytestmark = pytest.mark.postgres
KEY = 'isolated-test-key-with-at-least-32-bytes'
NOW = datetime(2026, 11, 13, 12, tzinfo=timezone.utc)


def test_parallel_budget_is_atomic_and_survives_engine_restart(postgres_engine):
    barrier = Barrier(12)
    rule = Budget('login-peer', ('peer', '192.0.2.1'), 5, 900)
    def attempt(_):
        barrier.wait(timeout=10)
        try:
            consume_budgets(postgres_engine, KEY, [rule], now=NOW)
            return True
        except AuthRateExceeded as exc:
            assert exc.retry_after == 900
            return False
    with ThreadPoolExecutor(12) as pool:
        assert list(pool.map(attempt, range(12))).count(True) == 5
    restarted = make_engine(postgres_engine.url.render_as_string(hide_password=False))
    try:
        with pytest.raises(AuthRateExceeded): consume_budgets(restarted, KEY, [rule], now=NOW)
        assert consume_budgets(restarted, KEY, [rule], now=NOW+timedelta(seconds=900))
    finally: restarted.dispose()
    with Session(postgres_engine) as db:
        rows = db.scalars(select(AccountRateBucket)).all()
        assert sorted(r.used for r in rows) == [1, 5]
        assert all('192.0.2.1' not in r.subject_hash and len(r.subject_hash) == 64 for r in rows)


def test_soft_delivery_limits_and_failed_operation_never_refund(postgres_engine):
    rules = [Budget('register-peer', ('peer', '192.0.2.1'), 10, 3600),
             Budget('register-email', ('email', 'test@example.org'), 1, 3600, soft=True)]
    assert consume_budgets(postgres_engine, KEY, rules, now=NOW)
    # Simulate the later account transaction failing; budgets are already committed.
    with Session(postgres_engine) as db: db.rollback()
    assert not consume_budgets(postgres_engine, KEY, rules, now=NOW)
    with Session(postgres_engine) as db:
        assert sorted(r.used for r in db.scalars(select(AccountRateBucket)).all()) == [1, 2]


def test_subjects_and_operation_scopes_are_independent(postgres_engine):
    for operation, subject in [('login-pair', ('a@example.org', '192.0.2.1')),
                               ('login-pair', ('a@example.org', '192.0.2.2')),
                               ('register-pair', ('a@example.org', '192.0.2.1'))]:
        rule = Budget(operation, subject, 1, 60)
        assert consume_budgets(postgres_engine, KEY, [rule], now=NOW)
        with pytest.raises(AuthRateExceeded): consume_budgets(postgres_engine, KEY, [rule], now=NOW)
    with Session(postgres_engine) as db:
        assert len(db.scalars(select(AccountRateBucket)).all()) == 3
