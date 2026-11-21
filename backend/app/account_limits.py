"""Shared, durable auth budgets. No request-forwarded headers or raw PII stored."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import math

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from .auth.accounts import AccountRateBucket


@dataclass(frozen=True)
class Budget:
    operation: str
    subject: tuple[str, ...]
    limit: int
    seconds: int
    soft: bool = False


class AuthRateExceeded(Exception):
    def __init__(self, retry_after):
        self.retry_after = retry_after


def consume_budgets(engine, key: str, budgets: list[Budget], *, now=None) -> bool:
    """Commit counters even on denial; caller's user/mail rollback cannot refund them.

    Soft email-only delivery limits return False without revealing account existence.
    Deterministic operation order prevents multi-budget deadlocks across workers.
    """
    now = now or datetime.now(timezone.utc)
    blocked, allowed = [], True
    insert = pg_insert if engine.dialect.name == 'postgresql' else sqlite_insert
    with engine.begin() as connection:
        for budget in sorted(budgets, key=lambda b: (b.operation, b.subject)):
            if budget.limit < 1 or budget.seconds < 1:
                raise ValueError('Invalid auth budget policy.')
            start = datetime.fromtimestamp(math.floor(now.timestamp()/budget.seconds)*budget.seconds, timezone.utc)
            end = start + timedelta(seconds=budget.seconds)
            subject = hmac.new(key.encode('utf-8'), json.dumps(budget.subject, separators=(',', ':')).encode(), hashlib.sha256).hexdigest()
            table = AccountRateBucket.__table__
            query = insert(table).values(operation=budget.operation, subject_hash=subject,
                                         window_start=start, used=1, expires_at=end)
            query = query.on_conflict_do_update(
                index_elements=[table.c.operation, table.c.subject_hash, table.c.window_start],
                set_={'used': table.c.used+1}, where=table.c.used < budget.limit,
            ).returning(table.c.used)
            if connection.scalar(query) is None:
                if budget.soft:
                    allowed = False
                else:
                    blocked.append(max(1, math.ceil((end-now).total_seconds())))
    if blocked:
        raise AuthRateExceeded(max(blocked))
    return allowed


def consume_mail_cooldown(engine, key, email, *, now):
    """Rolling60-second, all-peer verification cooldown; independent of user lookup.

    A stable bucket key plus atomic conditional upsert serializes parallel requests.
    Only the HMAC of the address is stored; registration/recovery hourly budgets remain.
    """
    table = AccountRateBucket.__table__
    operation = 'verification-cooldown'
    subject = hmac.new(key.encode('utf-8'), json.dumps(('email', email), separators=(',', ':')).encode(), hashlib.sha256).hexdigest()
    start = datetime(1970, 1, 1, tzinfo=timezone.utc)
    insert = pg_insert if engine.dialect.name == 'postgresql' else sqlite_insert
    with engine.begin() as connection:
        query = insert(table).values(operation=operation, subject_hash=subject, window_start=start,
                                     used=1, expires_at=now+timedelta(seconds=60))
        query = query.on_conflict_do_update(
            index_elements=[table.c.operation, table.c.subject_hash, table.c.window_start],
            set_={'expires_at': now+timedelta(seconds=60)}, where=table.c.expires_at <= now,
        ).returning(table.c.used)
        if connection.scalar(query) is not None:
            return
        deadline = connection.scalar(select(table.c.expires_at).where(
            table.c.operation == operation, table.c.subject_hash == subject, table.c.window_start == start))
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
    raise AuthRateExceeded(max(1, math.ceil((deadline-now).total_seconds())))
