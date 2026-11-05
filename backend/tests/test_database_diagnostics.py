import hashlib
import json
import sqlite3

import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.diagnostics import diagnose, main, read_engine
from app.main import COOKIE
from test_api import start, create


def test_current_database_report_is_readonly_redacted_and_preserves_file(client,application):
    start(client)
    watch=create(client)
    database=application.state.engine.url.database
    before=hashlib.sha256(open(database,'rb').read()).hexdigest()
    report=diagnose(application.state.engine.url.render_as_string(hide_password=False))
    assert report['status']=='revision_current' and report['observedRevisions']==['0011']
    assert report['manualCounts']=={'browser_sessions':1,'watches':1,'snapshots':1,'operation_records':0}
    assert client.cookies.get(COOKIE) not in json.dumps(report)
    assert watch['title'] not in json.dumps(report) and watch['id'] not in json.dumps(report)
    assert hashlib.sha256(open(database,'rb').read()).hexdigest()==before


def test_sqlite_connection_cannot_write_and_unicode_filename_works(tmp_path):
    database=tmp_path/'данные с пробелом.db'
    with sqlite3.connect(database) as connection:
        connection.execute('CREATE TABLE original (value TEXT)')
    engine=read_engine(f'sqlite:///{database}')
    try:
        with engine.connect() as connection:
            with pytest.raises(SQLAlchemyError):
                connection.execute(text("INSERT INTO original VALUES ('forbidden')"))
    finally:
        engine.dispose()
    with sqlite3.connect(database) as connection:
        assert connection.execute('SELECT count(*) FROM original').fetchone()==(0,)


def test_missing_database_is_not_created_and_restore_marker_is_respected(tmp_path):
    database=tmp_path/'missing.db'
    assert diagnose(f'sqlite:///{database}')['status']=='unavailable'
    assert not database.exists()
    with sqlite3.connect(database):
        pass
    (tmp_path/'restore.pending').write_text('incomplete',encoding='utf-8')
    assert diagnose(f'sqlite:///{database}')['status']=='restore_incomplete'


def test_legacy_and_unknown_revision_are_never_reported_current(tmp_path):
    database=tmp_path/'legacy.db'
    with sqlite3.connect(database) as connection:
        connection.execute('CREATE TABLE watches (private_value TEXT)')
    report=diagnose(f'sqlite:///{database}')
    assert report['status']=='schema_mismatch' and report['manualCounts']['snapshots'] is None
    with sqlite3.connect(database) as connection:
        connection.execute('CREATE TABLE alembic_version (version_num TEXT)')
        connection.execute("INSERT INTO alembic_version VALUES ('private-revision-value')")
    report=diagnose(f'sqlite:///{database}')
    assert report['observedRevisions']==['unknown']
    assert 'private-revision-value' not in json.dumps(report)


def test_configuration_and_driver_errors_do_not_leak_credentials(monkeypatch,capsys):
    value='postgresql+psycopg://user:secret-password@private-host/private-db'
    monkeypatch.setenv('DATABASE_URL',value)
    def fail(_):
        raise RuntimeError(value)
    monkeypatch.setattr('app.diagnostics.read_engine',fail)
    assert main()==1
    output=capsys.readouterr().out
    assert json.loads(output)['status']=='unavailable'
    assert all(secret not in output for secret in ('secret-password','private-host','private-db'))
