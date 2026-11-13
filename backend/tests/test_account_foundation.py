"""Native PG foundation tests; no claim that auth API exists in PR1."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from threading import Barrier

import pytest
from alembic import command
from sqlalchemy import delete, inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.accounts import AccountActionToken, AccountCsrfContext, AccountRateBucket, AccountRefreshToken, AccountSession, AccountUser
from app.database import BrowserSession, Watch
from app.maintenance import cleanup_expired_accounts
from native_support import postgres_engine  # noqa: F401
from test_migrations import config

pytestmark = pytest.mark.postgres
NOW = datetime(2026, 11, 13, tzinfo=timezone.utc)


def user(email='test@example.org'):
    return AccountUser(email=email, password_hash='synthetic-hash-not-a-credential', created_at=NOW,
                       updated_at=NOW, password_changed_at=NOW)


def session(user_id):
    return AccountSession(user_id=user_id, access_hash='a'*64, created_at=NOW,
                          access_expires_at=NOW+timedelta(minutes=15),
                          idle_expires_at=NOW+timedelta(days=7), expires_at=NOW+timedelta(days=30))


def test_unique_email_concurrent_transactions(postgres_engine):
    barrier = Barrier(2)
    def insert():
        with Session(postgres_engine) as db:
            db.add(user()); barrier.wait(timeout=10)
            try:
                db.commit(); return 'created'
            except IntegrityError:
                db.rollback(); return 'duplicate'
    with ThreadPoolExecutor(2) as pool:
        assert sorted(pool.map(lambda _: insert(), range(2))) == ['created', 'duplicate']
    with Session(postgres_engine) as db:
        assert len(db.scalars(select(AccountUser)).all()) == 1


@pytest.mark.parametrize('kind', ['email', 'status', 'purpose', 'foreign_key', 'lifetime', 'budget'])
def test_database_rejects_invalid_security_state(postgres_engine, kind):
    with Session(postgres_engine) as db:
        u = user(); db.add(u); db.flush()
        if kind == 'email': u.email = 'TEST@example.org'
        elif kind == 'status': u.status = 'unexpected'
        elif kind == 'purpose':
            db.add(AccountActionToken(token_hash='b'*64, user_id=u.id, purpose='login', created_at=NOW, expires_at=NOW+timedelta(hours=1)))
        elif kind == 'foreign_key': db.add(session('missing-user'))
        elif kind == 'lifetime':
            s = session(u.id); s.access_expires_at = s.expires_at+timedelta(seconds=1); db.add(s)
        else:
            db.add(AccountRateBucket(operation='login', subject_hash='c'*64, window_start=NOW, used=-1, expires_at=NOW+timedelta(hours=1)))
        with pytest.raises(IntegrityError): db.commit()


def test_account_cleanup_retains_spent_refresh_and_guest_history(postgres_engine):
    with Session(postgres_engine) as db:
        u = user(); db.add(u); db.flush(); s = session(u.id); db.add(s); db.flush()
        db.add(AccountRefreshToken(token_hash='b'*64, session_id=s.id, created_at=NOW, expires_at=NOW+timedelta(hours=1), consumed_at=NOW))
        db.add(AccountActionToken(token_hash='c'*64, user_id=u.id, purpose='verify_email', created_at=NOW-timedelta(hours=2), expires_at=NOW))
        db.add(AccountCsrfContext(token_hash='d'*64, csrf_token='synthetic-csrf', session_id=s.id, created_at=NOW-timedelta(hours=1), expires_at=NOW))
        db.add(AccountRateBucket(operation='login', subject_hash='e'*64, window_start=NOW-timedelta(hours=1), used=2, expires_at=NOW))
        db.add(BrowserSession(token_hash='f'*64, expires_at=NOW+timedelta(days=31))); db.flush()
        db.add(Watch(id='guest-watch', owner_hash='f'*64, university='Synthetic', title='Keep', source_url='https://example.org', created_at=NOW)); db.commit()
    counts = cleanup_expired_accounts(postgres_engine, now=NOW+timedelta(hours=2))
    assert counts == dict(account_action_tokens=1, account_csrf_contexts=1, account_rate_buckets=1, account_sessions=0)
    with Session(postgres_engine) as db:
        assert db.get(AccountRefreshToken, 'b'*64).consumed_at == NOW
        db.execute(delete(AccountUser)); db.commit()
        assert db.get(Watch, 'guest-watch').title == 'Keep'
        assert db.scalars(select(AccountSession)).all() == []
        assert db.scalars(select(AccountRefreshToken)).all() == []
    assert cleanup_expired_accounts(postgres_engine, now=NOW+timedelta(days=40))['account_sessions'] == 0


def test_guest_delete_cannot_delete_account(postgres_engine):
    with Session(postgres_engine) as db:
        db.add(user()); db.add(BrowserSession(token_hash='f'*64, expires_at=NOW)); db.commit()
        db.execute(delete(BrowserSession)); db.commit()
        assert len(db.scalars(select(AccountUser)).all()) == 1


def test_additive_migration_preserves_all_guest_tables(postgres_engine):
    cfg = config()
    with postgres_engine.connect() as conn:
        cfg.attributes['connection'] = conn
        command.downgrade(cfg, '0011')
        conn.execute(text("INSERT INTO browser_sessions VALUES (:token, :expiry)"), dict(token='f'*64, expiry=NOW))
        conn.execute(text("INSERT INTO watches VALUES ('guest', :token, 'Synthetic', 'Keep', 'https://example.org', :now)"), dict(token='f'*64, now=NOW))
        conn.execute(text("INSERT INTO snapshots VALUES ('snap', 'guest', :now, 10, 5, 0, 0, 'manual', 'manual-v1')"), dict(now=NOW)); conn.commit()
        tables = [t for t in inspect(conn).get_table_names() if t != 'alembic_version']
        before = {t: conn.execute(text(f'SELECT * FROM "{t}"')).all() for t in tables}
        command.upgrade(cfg, 'head'); command.check(cfg)
        assert set(inspect(conn).get_table_names()) - set(tables) == {'alembic_version', 'account_users', 'account_sessions', 'account_refresh_tokens', 'account_action_tokens', 'account_csrf_contexts', 'account_rate_buckets'}
        assert before == {t: conn.execute(text(f'SELECT * FROM "{t}"')).all() for t in tables}
        command.downgrade(cfg, '0011'); command.upgrade(cfg, 'head'); command.check(cfg)
        assert before == {t: conn.execute(text(f'SELECT * FROM "{t}"')).all() for t in tables}
