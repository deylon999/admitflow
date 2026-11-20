"""Native PostgreSQL publication integrity, immutable history and0013 upgrade."""
from datetime import datetime, timezone

import pytest
from alembic import command
from sqlalchemy import delete, func, insert, select, text, update
from sqlalchemy.exc import IntegrityError

from app.admissions import Campaign, CampaignProgram, CompetitionGroup, CompetitionGroupProgram, Program
from app.program_catalog_models import (ProgramCatalogDocument as Document, ProgramCatalogRevision as Revision,
    ProgramCatalogFact as Fact, ProgramCatalogGroupFact as GroupFact, ProgramCatalogPublication as Publication,
    ProgramCatalogImportAttempt as Attempt)
from native_support import postgres_engine  # noqa: F401
from test_program_identity_storage import seed, pid, alembic_config

pytestmark = pytest.mark.postgres
NOW = datetime(2026, 11, 21, tzinfo=timezone.utc)


def revision(rid, document='doc', campaign='c27'):
    return dict(id=rid, document_id=document, campaign_id=campaign, original_url='https://example.org/plan',
        final_url='https://example.org/plan', content_type='text/html', publication_date=None, fetched_at=NOW,
        checked_at=NOW, original_sha256=('a' if rid == 'r1' else 'b')*64, extractor_version='synthetic-v1',
        review_sha256='c'*64, normalized_sha256='d'*64, completeness='partial', program_count=1, group_count=1,
        university_name='Synthetic university')


def fact(rid, key='P1'):
    return dict(revision_id=rid, program_id=pid(key), campaign_id='c27', public_id='public-'+key, source_key=key,
        title='Synthetic programme', code='09.03.04', study_form=None, funding=None, category=None, seats=None,
        admission_totals=None, evidence={'synthetic': True}, search_text='synthetic programme', sort_text='synthetic programme')


def fill(db, rid):
    db.execute(insert(Revision).values(**revision(rid)))
    db.execute(insert(Fact).values(**fact(rid)))
    db.execute(insert(GroupFact).values(revision_id=rid, program_id=pid('P1'), group_id='g1', campaign_id='c27', facts={'seats': None}))


@pytest.fixture
def published(postgres_engine):
    seed(postgres_engine)
    with postgres_engine.begin() as db:
        db.execute(insert(CompetitionGroupProgram).values(group_id='g1',program_id=pid('P1'),campaign_id='c27'))
        db.execute(insert(Document).values(id='doc', campaign_id='c27', source_namespace='synthetic'))
        fill(db, 'r1')
        db.execute(insert(Publication).values(document_id='doc', revision_id='r1'))
        db.execute(insert(Attempt).values(document_id='doc', attempted_at=NOW, stage='publication',outcome='published',revision_id='r1'))
    return postgres_engine


@pytest.mark.parametrize('model,change', [(Revision, {'normalized_sha256':'f'*64}),
    (Fact, {'seats':0}), (GroupFact, {'facts':{'seats':0}}), (Attempt, {'outcome':'rejected'})])
@pytest.mark.parametrize('operation', ['update', 'delete'])
def test_revisions_facts_and_audit_are_append_only(published, model, change, operation):
    statement = update(model).values(**change) if operation == 'update' else delete(model)
    with pytest.raises(IntegrityError, match='program_catalog_immutable'), published.begin() as db:
        db.execute(statement)


@pytest.mark.parametrize('model,change', [(Campaign, {'year':2028}), (Program, {'source_key':'changed'}),
    (CompetitionGroup, {'funding':'paid'}), (Document, {'source_namespace':'changed'})])
def test_published_identity_cannot_be_reassigned(published, model, change):
    identifier = {'campaigns':'c27','programs':pid('P1'),'competition_groups':'g1','program_catalog_documents':'doc'}[model.__tablename__]
    with pytest.raises(IntegrityError, match='identity_immutable'), published.begin() as db:
        db.execute(update(model).where(model.id == identifier).values(**change))


def test_incomplete_revision_cannot_replace_previous_pointer(published):
    with published.begin() as db:
        db.execute(insert(Revision).values(**revision('r2')))
    with pytest.raises(IntegrityError, match='publication_incomplete'), published.begin() as db:
        db.execute(update(Publication).values(revision_id='r2'))
    with published.connect() as db:
        assert db.scalar(select(Publication.revision_id)) == 'r1'


def test_new_complete_revision_publishes_atomically_and_seals_old_history(published):
    with published.begin() as db:
        fill(db, 'r2')
        db.execute(update(Publication).values(revision_id='r2'))
        db.execute(insert(Attempt).values(document_id='doc', attempted_at=NOW, stage='publication', outcome='published',revision_id='r2'))
    with published.connect() as db:
        assert db.scalar(select(Publication.revision_id)) == 'r2'
        assert db.scalar(select(func.count()).select_from(Fact)) == 2
    # Even after the pointer moves, historical revisions cannot be extended.
    with pytest.raises(IntegrityError, match='revision_sealed'), published.begin() as db:
        db.execute(insert(Fact).values(**fact('r1','P2')))


def test_group_fact_requires_reviewed_identity_link(published):
    with published.begin() as db:
        db.execute(insert(Revision).values(**revision('r2')))
        db.execute(insert(Fact).values(**fact('r2','P2')))
    with pytest.raises(IntegrityError, match='fk_program_group_fact_link'), published.begin() as db:
        db.execute(insert(GroupFact).values(revision_id='r2', program_id=pid('P2'), group_id='g1', campaign_id='c27',facts={}))


def test_upgrade_populated0013_keeps_program_and_group_identity(postgres_engine):
    engine = postgres_engine
    with engine.connect() as connection:
        command.downgrade(alembic_config(connection),'0013')
    seed(engine)
    with engine.begin() as db:
        db.execute(insert(CompetitionGroupProgram).values(group_id='g1', program_id=pid('P1'), campaign_id='c27'))
    def identities():
        with engine.connect() as db:
            return {m.__tablename__:db.execute(select(m.__table__).order_by(*m.__table__.primary_key)).all() for m in [Program,CampaignProgram,CompetitionGroupProgram]}
    before = identities()
    with engine.connect() as connection:
        command.upgrade(alembic_config(connection),'head')
        command.upgrade(alembic_config(connection),'head')
        command.check(alembic_config(connection))
    assert identities() == before
    with engine.connect() as db:
        assert db.scalar(text('SELECT version_num FROM alembic_version')) == '0014'
        assert db.scalar(select(func.count()).select_from(Publication)) == 0
