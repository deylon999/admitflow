"""Native PostgreSQL integrity and upgrade rehearsal on owned isolated schemas.

All test institutions/programmes here are synthetic, never catalog evidence.
"""
from datetime import datetime, timezone
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, insert, select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.admissions import (Campaign, CampaignProgram, CandidateEntry, CompetitionGroup,
    CompetitionGroupProgram, Program, PublishedSnapshot, Source, SourceSnapshot, University)
from app.catalog_identity import program_id
from app.catalog_import import import_reviewed
from app.config import Settings
from app.main import create_app
from app.product_catalog import programs
from native_support import postgres_engine  # noqa: F401
from test_migrations import postgres_legacy_db  # noqa: F401
from test_product_catalog import assert_catalog_path

pytestmark = pytest.mark.postgres
NOW = datetime(2026, 11, 20, tzinfo=timezone.utc)


def seed(engine):
    with engine.begin() as db:
        for uid in ['head', 'other', 'branch']:
            db.execute(insert(University).values(id=uid, name='Synthetic ' + uid, region=None,
                parent_id='head' if uid == 'branch' else None, official_url='https://example.org/',
                provenance_url='https://example.org/', verified_at=NOW))
        for cid, uid, year, level in [('c26', 'head', 2026, 'bachelor'), ('c27', 'head', 2027, 'bachelor'),
                ('csp', 'head', 2027, 'specialist'), ('co', 'other', 2027, 'bachelor'), ('cb', 'branch', 2027, 'bachelor')]:
            db.execute(insert(Campaign).values(id=cid, university_id=uid, year=year, level=level))
        for key in ['P1', 'P2', 'standalone']:
            db.execute(insert(Program).values(**program_values(key)))
            db.execute(insert(CampaignProgram).values(program_id=pid(key), campaign_id='c27',
                                                      university_id='head', level='bachelor'))
        for gid, cid, funding, category in [('g1', 'c27', 'budget', 'general'),
                ('g2', 'c27', 'paid', 'general'), ('gq', 'c27', 'budget', 'separate-quota'),
                ('gold', 'c26', 'budget', 'general'), ('go', 'co', 'budget', 'general')]:
            db.execute(insert(CompetitionGroup).values(id=gid, campaign_id=cid, official_id=gid,
                title='Synthetic group', study_form='full-time', funding=funding, category=category,
                seats=None, coverage='candidate', rules_version=None))


def pid(key):
    return program_id('head', 'bachelor', 'c27', 'synthetic', key)


def program_values(key):
    return dict(id=pid(key), university_id='head', level='bachelor', origin_campaign_id='c27',
                source_namespace='synthetic', source_key=key)


@pytest.fixture
def populated(postgres_engine):
    seed(postgres_engine)
    return postgres_engine


def test_many_programs_per_group_many_groups_per_program_and_standalone(populated):
    links = [('g1', 'P1'), ('g1', 'P2'), ('g2', 'P1'), ('gq', 'P1')]
    with populated.begin() as db:
        db.execute(insert(CompetitionGroupProgram), [dict(group_id=g, program_id=pid(p), campaign_id='c27') for g, p in links])
        assert db.scalar(select(func.count()).select_from(CompetitionGroupProgram)) == 4
        assert db.scalar(select(func.count()).select_from(CompetitionGroupProgram)
                         .where(CompetitionGroupProgram.program_id == pid('standalone'))) == 0
        assert db.scalar(select(func.count()).select_from(CompetitionGroup).where(CompetitionGroup.seats.is_(None))) == 5
    # Identity-only rows never bypass the existing reviewed publication policy.
    with Session(populated) as db:
        assert programs(db) == []


def test_explicit_reviewed_cross_year_link_preserves_program_and_group_identity(populated):
    with populated.begin() as db:
        db.execute(insert(CampaignProgram).values(program_id=pid('P1'), campaign_id='c26', university_id='head', level='bachelor'))
        db.execute(insert(CompetitionGroupProgram).values(group_id='gold', program_id=pid('P1'), campaign_id='c26'))
        assert db.scalar(select(func.count()).select_from(CampaignProgram).where(CampaignProgram.program_id == pid('P1'))) == 2
        assert db.scalar(select(Program.origin_campaign_id).where(Program.id == pid('P1'))) == 'c27'
        assert db.scalar(select(CompetitionGroup.campaign_id).where(CompetitionGroup.id == 'gold')) == 'c26'


@pytest.mark.parametrize('changes', [{'university_id': 'other'}, {'university_id': 'branch'},
    {'level': 'specialist'}, {'origin_campaign_id': 'missing'}, {'source_key': ''}, {'source_namespace': ' '}])
def test_invalid_program_origin_is_rejected(populated, changes):
    values = {**program_values('new'), **changes}
    with pytest.raises(IntegrityError), populated.begin() as db:
        db.execute(insert(Program).values(**values))


@pytest.mark.parametrize('cid,uid,level', [('co', 'other', 'bachelor'), ('cb', 'branch', 'bachelor'),
    ('csp', 'head', 'specialist'), ('c27', 'other', 'bachelor'), ('c27', 'head', 'specialist')])
def test_campaign_program_cannot_mix_institutions_branches_or_levels(populated, cid, uid, level):
    # A duplicate PK must not mask the scope FK under test.
    with populated.begin() as db:
        db.execute(delete(CampaignProgram).where(CampaignProgram.program_id == pid('P1')))
    with pytest.raises(IntegrityError), populated.begin() as db:
        db.execute(insert(CampaignProgram).values(program_id=pid('P1'), campaign_id=cid, university_id=uid, level=level))


@pytest.mark.parametrize('group_id,campaign_id', [('gold', 'c27'), ('g1', 'c26'), ('go', 'c27'), ('missing', 'c27')])
def test_group_program_cannot_mix_years_or_institutions(populated, group_id, campaign_id):
    with pytest.raises(IntegrityError), populated.begin() as db:
        db.execute(insert(CompetitionGroupProgram).values(group_id=group_id, program_id=pid('P1'), campaign_id=campaign_id))


def test_group_program_requires_program_membership_in_that_campaign(populated):
    # The group/campaign pair exists; only the programme/campaign link is missing.
    with pytest.raises(IntegrityError), populated.begin() as db:
        db.execute(insert(CompetitionGroupProgram).values(group_id='gold', program_id=pid('P1'), campaign_id='c26'))


def test_natural_identity_collision_rolls_back_and_keeps_previous_links(populated):
    with populated.begin() as db:
        db.execute(insert(CompetitionGroupProgram).values(group_id='g1', program_id=pid('P1'), campaign_id='c27'))
    with pytest.raises(IntegrityError), populated.begin() as db:
        db.execute(insert(Program).values(**program_values('first-in-batch')))
        db.execute(insert(Program).values(**{**program_values('P1'), 'id': pid('different')}))
    with populated.connect() as db:
        assert db.scalar(select(func.count()).select_from(Program)) == 3
        assert db.scalar(select(func.count()).select_from(CompetitionGroupProgram)) == 1


@pytest.mark.parametrize('operation', ['duplicate', 'delete-program', 'delete-group', 'move-group-campaign'])
def test_existing_links_resist_duplicates_deletion_and_identity_changes(populated, operation):
    values = dict(group_id='g1', program_id=pid('P1'), campaign_id='c27')
    with populated.begin() as db:
        db.execute(insert(CompetitionGroupProgram).values(**values))
    operations = {
        'duplicate': insert(CompetitionGroupProgram).values(**values),
        'delete-program': delete(Program).where(Program.id == pid('P1')),
        'delete-group': delete(CompetitionGroup).where(CompetitionGroup.id == 'g1'),
        'move-group-campaign': update(CompetitionGroup).where(CompetitionGroup.id == 'g1').values(campaign_id='c26'),
    }
    with pytest.raises(IntegrityError), populated.begin() as db:
        db.execute(operations[operation])


def alembic_config(connection):
    config = Config(str(Path(__file__).resolve().parents[1] / 'alembic.ini'))
    config.attributes['connection'] = connection
    return config


def legacy_rows(engine):
    with engine.connect() as db:
        return {model.__tablename__: db.execute(select(model.__table__).order_by(*model.__table__.primary_key)).all()
                for model in [University, Campaign, CompetitionGroup, Source, SourceSnapshot, CandidateEntry, PublishedSnapshot]}


def test_upgrade_populated_0012_preserves_sources_snapshots_ids_and_public_api(postgres_legacy_db):
    engine = postgres_legacy_db
    with engine.connect() as connection:
        command.upgrade(alembic_config(connection), '0012')
    import_reviewed(engine)
    with engine.begin() as db:
        db.execute(insert(Source).values(id='synthetic-source', group_id='sgu-2026-4588', url='https://example.org/',
            domain='example.org', adapter_version='synthetic-v1', enabled=False, snapshot_kind='archive'))
        db.execute(insert(SourceSnapshot).values(id='synthetic-snapshot', source_id='synthetic-source',
            group_id='sgu-2026-4588', payload_hash='a'*64, fetched_at=NOW, kind='archive', row_count=1, complete=True))
        db.execute(insert(CandidateEntry).values(snapshot_id='synthetic-snapshot', candidate_key='synthetic',
            official_rank=1, score=None, consent=None, priority=None, participation='unknown'))
        db.execute(insert(PublishedSnapshot).values(source_id='synthetic-source', snapshot_id='synthetic-snapshot'))
    before = legacy_rows(engine)
    with Session(engine) as db:
        public_before = {p.id: p for p in programs(db)}
    with engine.connect() as connection:
        command.upgrade(alembic_config(connection), 'head')
        command.upgrade(alembic_config(connection), 'head')
        command.check(alembic_config(connection))
    assert legacy_rows(engine) == before
    with engine.connect() as db:
        assert db.scalar(text('SELECT version_num FROM alembic_version')) == '0015'
        assert db.scalar(select(func.count()).select_from(Program)) == 0  # No inferred 1:1 backfill.
    with Session(engine) as db:
        assert {p.id: p for p in programs(db)} == public_before
    import_reviewed(engine)
    assert legacy_rows(engine) == before
    # HTTP lifespan also seeds the pre-existing reference universities. Check
    # migration/import preservation before that independent startup operation.
    app = create_app(Settings(database_url=engine.url.render_as_string(hide_password=False), auto_create_schema=False))
    with TestClient(app) as client:
        assert_catalog_path(client)


def test_downgrade_on_disposable_schema_preserves_legacy_rows(postgres_legacy_db):
    engine = postgres_legacy_db
    with engine.connect() as connection:
        command.upgrade(alembic_config(connection), 'head')
    import_reviewed(engine)
    before = legacy_rows(engine)
    with engine.connect() as connection:
        command.downgrade(alembic_config(connection), '0012')
        command.upgrade(alembic_config(connection), 'head')
        command.check(alembic_config(connection))
    assert legacy_rows(engine) == before
