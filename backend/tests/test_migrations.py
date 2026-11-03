import importlib.util
import io
import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import CheckConstraint, inspect, text
from pg_support import isolated_postgres

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
    assert len(inspect(migration_db).get_table_names()) == 16  # 15 domain + revision.
    with migration_db.connect() as db:
        assert db.scalar(text('SELECT version_num FROM alembic_version')) == '0006'


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


@pytest.mark.parametrize('table_name,constraint,expression',[
    ('snapshots','rank_range','rank > 999999'),
    ('snapshots','groups_above','excluded >= 0 AND (no_consent >= 0 OR excluded + no_consent < rank)'),
    ('competition_groups','group_coverage',"coverage IN ('candidate', 'MANUAL', 'automatic', 'suspended')"),
    ('competition_groups','group_coverage',"coverage IN ('candidate', 'man ual', 'automatic', 'suspended')"),
])
def test_changed_check_constraint_is_not_silently_adopted(migration_db,table_name,constraint,expression):
    schema = frozen_schema()
    table = schema.tables[table_name]
    original = next(item for item in table.constraints if isinstance(item, CheckConstraint) and item.name == constraint)
    table.constraints.remove(original)
    table.append_constraint(CheckConstraint(expression, name=constraint))
    schema.create_all(migration_db)
    with pytest.raises(RuntimeError, match='Unexpected check constraints'):
        command.upgrade(config(), 'head')


def test_changed_operations_boolean_grouping_is_not_adopted(migration_db):
    create_original_development_schema(migration_db)
    with migration_db.begin() as db:
        db.execute(text('DROP TABLE operation_records'))
    spec=importlib.util.spec_from_file_location('operations_schema',BACKEND/'alembic/versions/0002_operation_records.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    table=module._table()
    check=next(item for item in table.constraints if isinstance(item,CheckConstraint))
    table.constraints.remove(check)
    table.append_constraint(CheckConstraint('(response_status = 201 AND response IS NOT NULL OR response_status = 410) AND response IS NULL',name='operation_response_state'))
    table.create(migration_db)
    with pytest.raises(RuntimeError,match='incompatible constraints'):
        command.upgrade(config(),'head')


@pytest.fixture
def postgres_legacy_db(monkeypatch):
    if not os.getenv('TEST_DATABASE_URL'):
        pytest.skip('Requires a disposable PostgreSQL test database')
    with isolated_postgres(os.environ['TEST_DATABASE_URL']) as engine:
        monkeypatch.setenv('DATABASE_URL',engine.url.render_as_string(hide_password=False))
        monkeypatch.setenv('ENVIRONMENT','development')
        yield engine


@pytest.mark.parametrize('full_schema',[False,True],ids=['manual-snapshots','full-with-operations'])
@pytest.mark.postgres
def test_postgres_adopts_legacy_schema_and_keeps_history(postgres_legacy_db,full_schema):
    seed_legacy(postgres_legacy_db)
    if full_schema:
        create_original_development_schema(postgres_legacy_db)
    command.upgrade(config(),'head')
    command.upgrade(config(),'head')
    command.check(config())
    with postgres_legacy_db.connect() as db:
        assert db.scalar(text('SELECT version_num FROM alembic_version'))=='0006'
        assert db.scalar(text('SELECT title FROM watches'))=='Test direction'
        assert db.execute(text('SELECT id, watch_id, rank - excluded - no_consent FROM snapshots')).one()==('snapshot-1','watch-1',74)
        assert not db.scalar(text("SELECT count(*) FROM pg_class WHERE relname LIKE '_admitflow_check_%' AND relnamespace=pg_my_temp_schema()"))


@pytest.mark.parametrize('case',['rank-operator','literal-case','not-valid','operations-logic'])
@pytest.mark.postgres
def test_postgres_refuses_incompatible_legacy_checks(postgres_legacy_db,case):
    seed_legacy(postgres_legacy_db)
    create_original_development_schema(postgres_legacy_db)
    changes={
        'rank-operator':('snapshots','rank_range','rank > 1 AND rank <= 1000000',''),
        'literal-case':('competition_groups','group_coverage',"coverage IN ('candidate', 'MANUAL', 'automatic', 'suspended')",''),
        'not-valid':('snapshots','rank_range','rank >= 1 AND rank <= 1000000',' NOT VALID'),
        'operations-logic':('operation_records','operation_response_state','(response_status = 201 AND response IS NOT NULL) AND (response_status = 410 AND response IS NULL)',''),
    }
    table,name,expression,suffix=changes[case]
    with postgres_legacy_db.begin() as db:
        # All identifiers/expressions are fixed test constants, never user input.
        db.execute(text(f'ALTER TABLE {table} DROP CONSTRAINT {name}'))
        db.execute(text(f'ALTER TABLE {table} ADD CONSTRAINT {name} CHECK ({expression}){suffix}'))
    with pytest.raises(RuntimeError,match='Unexpected check constraints|incompatible constraints'):
        command.upgrade(config(),'head')
    with postgres_legacy_db.connect() as db:
        assert db.scalar(text('SELECT count(*) FROM snapshots'))==1
        assert db.scalar(text('SELECT count(*) FROM watches'))==1


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


@pytest.mark.postgres
def test_postgres_real_upgrade_and_downgrade(postgres_legacy_db):
    command.upgrade(config(), 'head')
    command.check(config())
    with postgres_legacy_db.begin() as db:
        db.execute(text('SELECT * FROM candidate_entries LIMIT 1'))
    command.downgrade(config(), 'base')
    command.upgrade(config(), 'head')
    command.check(config())


def assert_assessment_cascade_upgrade_keeps_data(engine):
    from datetime import datetime,timezone
    from sqlalchemy import delete,func,select
    from sqlalchemy.orm import Session
    from app.database import BrowserSession
    from app.admissions import Assessment,Campaign,CompetitionGroup,Source,SourceSnapshot,Subscription,University
    command.upgrade(config(),'0004')
    now=datetime(2026,11,3,tzinfo=timezone.utc)
    with Session(engine) as db:
        db.add(BrowserSession(token_hash='b'*64,expires_at=now));db.flush()
        db.add(University(id='cascade-u',name='Synthetic migration only',official_url='https://example.org',provenance_url='https://example.org',verified_at=now));db.flush()
        db.add(Campaign(id='cascade-c',university_id='cascade-u',year=2026,level='bachelor'));db.flush()
        db.add(CompetitionGroup(id='cascade-g',campaign_id='cascade-c',official_id='test',title='Synthetic migration',study_form='full-time',funding='budget',category='general',seats=1,coverage='candidate'));db.flush()
        db.add(Source(id='cascade-source',group_id='cascade-g',url='https://example.org/list',domain='example.org',enabled=False));db.flush()
        db.add(SourceSnapshot(id='cascade-snapshot',source_id='cascade-source',group_id='cascade-g',payload_hash='a'*64,fetched_at=now,kind='archive',row_count=0,complete=False));db.flush()
        db.add(Subscription(id='cascade-sub',owner_hash='b'*64,group_id='cascade-g',candidate_key='c'*64,created_at=now));db.flush()
        db.add(Assessment(id='cascade-assessment',subscription_id='cascade-sub',group_id='cascade-g',snapshot_id='cascade-snapshot',rules_version='old-v1',assessed_at=now,state='unsupported',facts={'marker':'preserve'},assumptions=['Synthetic migration proof']));db.commit()
    for target in ('head','0004','head'):
        if target=='0004':command.downgrade(config(),target)
        else:command.upgrade(config(),target)
        with Session(engine) as db:
            row=db.get(Assessment,'cascade-assessment')
            assert row.facts=={'marker':'preserve'} and row.subscription_id=='cascade-sub' and row.snapshot_id=='cascade-snapshot'
    command.check(config())
    constraint=next(row for row in inspect(engine).get_foreign_keys('assessments') if row['name']=='fk_assessment_subscription_group')
    assert constraint['options']['ondelete']=='CASCADE'
    with Session(engine) as db:
        db.execute(delete(BrowserSession).where(BrowserSession.token_hash=='b'*64));db.commit()
        assert db.scalar(select(func.count()).select_from(Subscription))==0
        assert db.scalar(select(func.count()).select_from(Assessment))==0
        assert db.scalar(select(func.count()).select_from(SourceSnapshot))==1


def test_assessment_cascade_upgrade_preserves_existing_data(migration_db):
    assert_assessment_cascade_upgrade_keeps_data(migration_db)


@pytest.mark.postgres
def test_postgres_assessment_cascade_upgrade_preserves_existing_data(postgres_legacy_db):
    assert_assessment_cascade_upgrade_keeps_data(postgres_legacy_db)
