import importlib.util
import io
import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import CheckConstraint, inspect, text
from sqlalchemy.engine import make_url

from app.database import Base, make_engine

BACKEND = Path(__file__).resolve().parents[1]


def config():
    return Config(str(BACKEND / 'alembic.ini'))


def frozen_schema():
    spec = importlib.util.spec_from_file_location('initial_schema', BACKEND / 'alembic/versions/0001_initial.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module._schema()


@pytest.fixture
def migration_db(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'migration.db'}"
    monkeypatch.setenv('DATABASE_URL', url)
    monkeypatch.setenv('ENVIRONMENT', 'development')
    engine = make_engine(url)
    yield engine
    engine.dispose()


def test_empty_database_upgrade_repeat_and_model_alignment(migration_db):
    command.upgrade(config(), 'head')
    command.upgrade(config(), 'head')
    command.check(config())
    assert len(inspect(migration_db).get_table_names()) == 14  # 13 domain + revision.
    with migration_db.connect() as db:
        assert db.scalar(text('SELECT version_num FROM alembic_version')) == '0003'


def seed_legacy(engine):
    schema = frozen_schema()
    for name in ('browser_sessions', 'watches', 'snapshots'):
        schema.tables[name].create(engine)
    with engine.begin() as db:
        db.execute(text("INSERT INTO browser_sessions VALUES (:token, '2030-01-01')"), {'token': 'a' * 64})
        db.execute(text("INSERT INTO watches VALUES ('watch-1', :token, 'Synthetic university', 'Test direction', 'https://example.org/list', '2026-01-01')"), {'token': 'a' * 64})
        db.execute(text("INSERT INTO snapshots VALUES ('snapshot-1', 'watch-1', '2026-01-01', 120, 90, 30, 16, 'manual', 'manual-v1')"))


def test_legacy_schema_is_adopted_without_losing_manual_history(migration_db):
    seed_legacy(migration_db)
    command.upgrade(config(), 'head')
    command.check(config())
    with migration_db.connect() as db:
        assert db.scalar(text('SELECT title FROM watches')) == 'Test direction'
        assert db.scalar(text('SELECT rank - excluded - no_consent FROM snapshots')) == 74


def create_original_development_schema(engine):
    frozen_schema().create_all(engine)
    spec = importlib.util.spec_from_file_location('operations_schema', BACKEND / 'alembic/versions/0002_operation_records.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module._table().create(engine)


def test_original_development_create_all_schema_is_also_adopted(migration_db):
    seed_legacy(migration_db)
    create_original_development_schema(migration_db)
    command.upgrade(config(), 'head')
    command.check(config())
    with migration_db.connect() as db:
        assert db.scalar(text('SELECT count(*) FROM watches')) == 1


def test_incompatible_existing_operations_are_not_stamped_over(migration_db):
    create_original_development_schema(migration_db)
    with migration_db.begin() as db:
        db.execute(text('ALTER TABLE operation_records ADD COLUMN unexpected TEXT'))
    with pytest.raises(RuntimeError, match='differs from migration 0002'):
        command.upgrade(config(), 'head')


def test_future_unversioned_schema_is_not_guessed_or_stamped(migration_db):
    Base.metadata.create_all(migration_db)
    with pytest.raises(RuntimeError, match='differs from the initial schema'):
        command.upgrade(config(), 'head')


def test_import_migration_preserves_existing_snapshot_and_references(migration_db):
    command.upgrade(config(),'0002')
    with migration_db.begin() as db:
        db.execute(text("INSERT INTO universities (id,name,official_url,provenance_url,verified_at) VALUES ('u','Synthetic','https://example.org','https://example.org/list','2026-01-01')"))
        db.execute(text("INSERT INTO campaigns VALUES ('c','u',2026,'bachelor')"))
        db.execute(text("INSERT INTO competition_groups (id,campaign_id,official_id,title,study_form,funding,category,seats,coverage) VALUES ('g','c','test','Synthetic','full-time','budget','general',10,'candidate')"))
        db.execute(text("INSERT INTO sources (id,group_id,url,domain,enabled) VALUES ('s','g','https://example.org/list','example.org',0)"))
        db.execute(text("INSERT INTO source_snapshots (id,source_id,group_id,payload_hash,fetched_at,kind,row_count,complete) VALUES ('snap','s','g',:hash,'2026-01-01','archive',1,1)"),{'hash':'a'*64})
        db.execute(text("INSERT INTO candidate_entries (snapshot_id,candidate_key,official_rank,participation) VALUES ('snap','synthetic',1,'unknown')"))
        db.execute(text("INSERT INTO published_snapshots VALUES ('s','snap')"))
    command.upgrade(config(),'head')
    command.check(config())
    with migration_db.connect() as db:
        assert db.scalar(text('SELECT snapshot_id FROM published_snapshots')) == 'snap'
        assert db.scalar(text('SELECT count(*) FROM candidate_entries')) == 1
        assert db.scalar(text('SELECT adapter_version FROM source_snapshots')) is None
        assert db.execute(text('PRAGMA foreign_key_check')).all() == []


def test_incompatible_schema_stops_before_domain_tables_are_changed(migration_db):
    seed_legacy(migration_db)
    with migration_db.begin() as db:
        db.execute(text('ALTER TABLE watches ADD COLUMN unexpected TEXT'))
    with pytest.raises(RuntimeError, match='differs from the initial schema'):
        command.upgrade(config(), 'head')
    assert 'universities' not in inspect(migration_db).get_table_names()
    with migration_db.connect() as db:
        assert db.scalar(text('SELECT count(*) FROM snapshots')) == 1


def test_downgrade_and_upgrade_on_disposable_database(migration_db):
    command.upgrade(config(), 'head')
    command.downgrade(config(), 'base')
    assert inspect(migration_db).get_table_names() == ['alembic_version']
    command.upgrade(config(), 'head')
    command.check(config())


def test_changed_check_constraint_is_not_silently_adopted(migration_db):
    schema = frozen_schema()
    table = schema.tables['snapshots']
    original = next(item for item in table.constraints if isinstance(item, CheckConstraint) and item.name == 'rank_range')
    table.constraints.remove(original)
    table.append_constraint(CheckConstraint('rank > 999999', name='rank_range'))
    for name in ('browser_sessions', 'watches', 'snapshots'):
        schema.tables[name].create(migration_db)
    with pytest.raises(RuntimeError, match='Unexpected check constraints'):
        command.upgrade(config(), 'head')


def test_postgres_offline_sql_compiles_without_a_server(monkeypatch):
    monkeypatch.setenv('DATABASE_URL', 'postgresql+psycopg://test:test@localhost/admitflow_test')
    monkeypatch.setenv('ENVIRONMENT', 'development')
    output = io.StringIO()
    cfg = Config(str(BACKEND / 'alembic.ini'), output_buffer=output)
    command.upgrade(cfg, 'head', sql=True)
    sql = output.getvalue()
    assert 'CREATE TABLE source_snapshots' in sql
    assert 'fk_assessment_snapshot_group' in sql
    assert "INSERT INTO alembic_version" in sql


@pytest.mark.skipif(not os.getenv('TEST_DATABASE_URL'), reason='Requires a disposable PostgreSQL test database')
def test_postgres_real_upgrade_and_downgrade(monkeypatch):
    url = os.environ['TEST_DATABASE_URL']
    if not (make_url(url).database or '').startswith('admitflow_test'):
        raise RuntimeError('TEST_DATABASE_URL must name a disposable admitflow_test* database')
    monkeypatch.setenv('DATABASE_URL', url)
    monkeypatch.setenv('ENVIRONMENT', 'development')
    engine = make_engine(url)
    try:
        command.upgrade(config(), 'head')
        command.check(config())
        with engine.begin() as db:
            db.execute(text('SELECT * FROM candidate_entries LIMIT 1'))
        command.downgrade(config(), 'base')
        command.upgrade(config(), 'head')
        command.check(config())
    finally:
        engine.dispose()
