"""Read-only database evidence. Does not migrate, seed or repair anything."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.pool import NullPool

from .database import make_engine

MANUAL_TABLES = ('browser_sessions', 'watches', 'snapshots', 'operation_records')


def read_engine(value):
    url = make_url(value)
    if url.get_backend_name() == 'postgresql':
        return make_engine(value)
    if url.get_backend_name() != 'sqlite' or url.query or url.database in (None, '', ':memory:'):
        raise ValueError('unsupported_database')
    database = Path(url.database).resolve()
    if not database.is_file():
        raise ValueError('database_missing')
    marker = database.parent/'restore.pending'
    if marker.exists() or marker.is_symlink():
        raise ValueError('restore_incomplete')
    # mode=ro also prevents a missing file from being created during a race.
    return create_engine('sqlite://', creator=lambda: sqlite3.connect(database.as_uri()+'?mode=ro', uri=True), poolclass=NullPool)


def diagnose(value):
    report = {'format': 'database-diagnostic-v1', 'generatedAt': datetime.now(timezone.utc).isoformat(),
              'status': 'unavailable', 'dialect': 'unknown', 'readOnly': True,
              'expectedRevisions': [], 'observedRevisions': [], 'manualCounts': None}
    engine = None
    try:
        backend = make_url(value).get_backend_name()
        if backend in ('sqlite', 'postgresql'):
            report['dialect'] = backend
        script = ScriptDirectory.from_config(Config(str(Path(__file__).resolve().parents[1]/'alembic.ini')))
        expected = set(script.get_heads())
        known = {revision.revision for revision in script.walk_revisions()}
        report['expectedRevisions'] = sorted(expected)
        engine = read_engine(value)
        with engine.connect() as connection:
            if backend == 'postgresql':
                connection.exec_driver_sql('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
                connection.exec_driver_sql("SET LOCAL statement_timeout = '5000ms'")
                connection.exec_driver_sql("SET LOCAL lock_timeout = '2000ms'")
            else:
                connection.exec_driver_sql('PRAGMA query_only=ON')
                connection.exec_driver_sql('BEGIN')
            tables = set(inspect(connection).get_table_names())
            revisions = connection.execute(text('SELECT version_num FROM alembic_version LIMIT 20')).scalars().all() if 'alembic_version' in tables else []
            # Unknown revision text could itself contain private values.
            observed = [item if isinstance(item,str) and item in known else 'unknown' for item in revisions]
            report['observedRevisions'] = sorted(observed)
            report['manualCounts'] = {name: connection.scalar(text(f'SELECT count(*) FROM {name}')) if name in tables else None for name in MANUAL_TABLES}
            report['status'] = 'revision_current' if set(observed) == expected and all(value is not None for value in report['manualCounts'].values()) else 'schema_mismatch'
    except Exception as error:
        # Never stringify driver/config errors: they can include DSNs and secrets.
        if isinstance(error, ValueError) and error.args == ('restore_incomplete',):
            report['status'] = 'restore_incomplete'
        else:
            report['status'] = 'unavailable'
        report['manualCounts'] = None
    finally:
        if engine is not None:
            try:
                engine.dispose()
            except Exception:
                report['status'] = 'unavailable'
    return report


def main():
    report = diagnose(os.getenv('DATABASE_URL', 'sqlite:///./abiturient.db'))
    print(json.dumps(report, ensure_ascii=True, sort_keys=True))
    return 0 if report['status'] == 'revision_current' else 1


if __name__ == '__main__':
    raise SystemExit(main())
