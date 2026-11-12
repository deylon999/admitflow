"""CI-only migration gate. Requires an empty disposable PostgreSQL database."""
import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect

from app.database import make_engine
from pg_support import disposable_postgres_url


def check_alignment(connection, config):
    expected = set(ScriptDirectory.from_config(config).get_heads())
    current = set(MigrationContext.configure(connection).get_current_heads())
    if not expected or current != expected:
        raise RuntimeError(f'Migration heads differ: current={sorted(current)}, expected={sorted(expected)}')
    print(f'Migration heads match: {sorted(current)}', flush=True)
    config.attributes['connection'] = connection
    command.check(config)


def verify_clean_database(connection):
    if connection.dialect.name != 'postgresql':
        raise ValueError('Migration gate requires PostgreSQL')
    inspector = inspect(connection)
    if inspector.get_table_names() or inspector.get_view_names():
        raise RuntimeError('Migration gate requires an empty disposable database; no existing objects are modified')
    config = Config(str(Path(__file__).resolve().parents[1] / 'alembic.ini'))
    config.attributes['connection'] = connection
    print('Empty PostgreSQL database confirmed; upgrading to head', flush=True)
    command.upgrade(config, 'head')
    # NEG-03: drift only in this disposable test database.
    connection.exec_driver_sql('ALTER TABLE universities ADD COLUMN ci_negative_drift INTEGER')
    connection.commit()
    check_alignment(connection, config)
    print('Migration verification passed', flush=True)


def main():
    # Never fall back to DATABASE_URL or the application's SQLite default.
    url = disposable_postgres_url(os.environ.get('MIGRATION_DATABASE_URL', ''))
    if url.query or not url.database.endswith('_migrations'):
        raise ValueError('MIGRATION_DATABASE_URL must name admitflow_test*_migrations without connection options')
    engine = make_engine(url.render_as_string(hide_password=False))
    try:
        with engine.connect() as connection:
            verify_clean_database(connection)
    finally:
        engine.dispose()


if __name__ == '__main__':
    main()
