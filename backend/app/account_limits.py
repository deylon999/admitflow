"""Shared, durable auth budgets. No request-forwarded headers or raw PII stored."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import math

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from .accounts import AccountRateBucket


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
