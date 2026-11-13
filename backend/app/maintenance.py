"""Maintenance commands, independent of the HTTP application."""
import argparse
from datetime import datetime, timezone

from sqlalchemy import delete
from sqlalchemy.orm import Session

from .accounts import AccountActionToken, AccountCsrfContext, AccountRateBucket, AccountSession
from .config import Settings
from .database import BrowserSession, make_engine


def cleanup_expired_sessions(engine, *, now=None):
    cutoff = now or datetime.now(timezone.utc)
    with Session(engine) as db:
        result = db.execute(delete(BrowserSession).where(BrowserSession.expires_at <= cutoff))
        db.commit()
        return result.rowcount


def cleanup_expired_accounts(engine, *, now=None):
    """Keep spent refresh hashes until absolute expiry so replay remains detectable."""
    cutoff = now or datetime.now(timezone.utc)
    with Session(engine) as db:
        counts = {}
        for model in (AccountActionToken, AccountCsrfContext, AccountRateBucket, AccountSession):
            result = db.execute(delete(model).where(model.expires_at <= cutoff))
            counts[model.__tablename__] = result.rowcount
        db.commit()
        return counts


def main():
    parser = argparse.ArgumentParser(description='Application maintenance')
    parser.add_argument('command', choices=['cleanup-sessions', 'cleanup-accounts'])
    args = parser.parse_args()
    engine = make_engine(Settings.from_env().database_url)
    try:
        if args.command == 'cleanup-accounts':
            print(f'Deleted expired account records: {cleanup_expired_accounts(engine)}')
        else:
            print(f'Deleted expired sessions: {cleanup_expired_sessions(engine)}')
    finally:
        engine.dispose()


if __name__ == '__main__':
    main()
