"""Maintenance commands, independent of the HTTP application."""
import argparse
from datetime import datetime, timezone

from sqlalchemy import delete
from sqlalchemy.orm import Session

from .config import Settings
from .database import BrowserSession, make_engine


def cleanup_expired_sessions(engine, *, now=None):
    cutoff = now or datetime.now(timezone.utc)
    with Session(engine) as db:
        result = db.execute(delete(BrowserSession).where(BrowserSession.expires_at <= cutoff))
        db.commit()
        return result.rowcount


def main():
    parser = argparse.ArgumentParser(description='Application maintenance')
    parser.add_argument('command', choices=['cleanup-sessions'])
    parser.parse_args()
    engine = make_engine(Settings.from_env().database_url)
    try:
        print(f'Deleted expired sessions: {cleanup_expired_sessions(engine)}')
    finally:
        engine.dispose()


if __name__ == '__main__':
    main()
