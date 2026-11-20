"""NativePG pipeline tests use synthetic originals in real university ID scopes.

No synthetic document is shipped in the default reviewed source package.
"""
from copy import deepcopy
from datetime import datetime, timedelta
import hashlib

import pytest
from sqlalchemy import func, insert, select
from sqlalchemy.orm import Session

from app.admissions import Campaign, CompetitionGroup, CompetitionGroupProgram, Program, Source, University
from app.catalog_identity import campaign_id, program_id
from app.catalog_import import import_reviewed
from app.program_catalog_models import (ProgramCatalogDocument as Document, ProgramCatalogRevision as Revision,
    ProgramCatalogFact as Fact, ProgramCatalogGroupFact as GroupFact, ProgramCatalogPublication as Publication,
    ProgramCatalogImportAttempt as Attempt)
from app.program_catalog_import import import_document, import_sources
from app.program_catalog_review import EXTRACTORS, load_reviews
from app.sources.storage import RawStore, StorageError
from native_support import postgres_engine  # noqa: F401
from test_program_catalog_review import package

pytestmark = pytest.mark.postgres


def source(kind='hse'):
    body, synthetic = package(kind)
    base = deepcopy(load_reviews()[0 if kind == 'hse' else 1])
    base.update(synthetic)
    base['review_method'] = 'Synthetic pipeline fixture, not real source evidence'
    return body, base


@pytest.fixture
def store(tmp_path):
    return RawStore(tmp_path/'raw')


def counts(engine):
    with engine.connect() as db:
        return {m.__tablename__:db.scalar(select(func.count()).select_from(m)) for m in [Document,Revision,Fact,GroupFact,Publication,Attempt,Program]}


@pytest.mark.parametrize('kind', ['hse','sgu'])
def test_import_repeat_provenance_and_nulls(postgres_engine, store, kind):
    body, review = source(kind)
    first = import_document(postgres_engine,review,body,store)
    second = import_document(postgres_engine,review,body,store)
    assert first['outcome'] == 'published' and second['outcome'] == 'unchanged'
    assert first['revisionId'] == second['revisionId']
    with Session(postgres_engine) as db:
        assert db.scalar(select(func.count()).select_from(Revision)) == 1
        assert db.scalar(select(func.count()).select_from(Fact)) == 2
        assert db.scalar(select(func.count()).select_from(GroupFact)) == 0
        assert db.scalar(select(func.count()).select_from(Source)) == 0
        revision = db.get(Revision,first['revisionId'])
        assert revision.original_sha256 == review['original_sha256']
        assert revision.original_url == review['url'] and revision.publication_date is None
        assert revision.completeness == 'partial' and revision.group_count == 0
        rows = db.scalars(select(Fact)).all()
        assert all(r.funding is r.category is r.seats is None for r in rows)
        assert all(r.evidence['originalSha256'] == review['original_sha256'] for r in rows)
        if kind == 'sgu':
            assert rows[0].admission_totals['target_quota'] is None
    assert store.read(review['original_sha256']) == body


def test_approved_new_version_preserves_ids_and_old_facts(postgres_engine,store):
    body, review = source()
    first = import_document(postgres_engine,review,body,store)
    changed = deepcopy(review)
    new_body = body.replace(b'Example Fashion', b'Updated Fashion')
    changed['original_sha256'] = hashlib.sha256(new_body).hexdigest()
    changed['checked_at'] = (datetime.fromisoformat(review['checked_at'])+timedelta(seconds=1)).isoformat()
    changed['programs'][0]['title'] = 'Updated Fashion'
    second = import_document(postgres_engine,changed,new_body,store)
    assert second['outcome'] == 'published' and second['revisionId'] != first['revisionId']
    with Session(postgres_engine) as db:
        old = {r.source_key:r for r in db.scalars(select(Fact).where(Fact.revision_id == first['revisionId']))}
        new = {r.source_key:r for r in db.scalars(select(Fact).where(Fact.revision_id == second['revisionId']))}
        assert old['/ba/program/fashion'].title == 'Example Fashion'
        assert new['/ba/program/fashion'].title == 'Updated Fashion'
        assert {k:(r.program_id,r.public_id) for k,r in old.items()} == {k:(r.program_id,r.public_id) for k,r in new.items()}
    replay = import_document(postgres_engine,review,body,store)
    assert replay['outcome'] == 'rejected' and replay['error'] == 'catalog_historical_revision_replay'
    with Session(postgres_engine) as db:
        assert db.get(Publication,first['documentId']).revision_id == second['revisionId']


@pytest.mark.parametrize('failure', ['hash','dropped-program','empty','unsupported-extractor'])
def test_rejected_source_keeps_previous_revision(postgres_engine,store,failure):
    body, review = source()
    first = import_document(postgres_engine,review,body,store)
    changed = deepcopy(review)
    if failure == 'hash': body += b' '
    elif failure == 'dropped-program':
        changed['selection'] = changed['selection'][:1]
        changed['programs'] = changed['programs'][:1]
    elif failure == 'empty': changed['selection'] = []
    else: changed['extractor_version'] = 'unknown'
    rejected = import_document(postgres_engine,changed,body,store)
    assert rejected['outcome'] == 'rejected'
    with Session(postgres_engine) as db:
        assert db.get(Publication,first['documentId']).revision_id == first['revisionId']
        assert db.scalar(select(func.count()).select_from(Revision)) == 1
        assert db.scalar(select(func.count()).select_from(Fact)) == 2
        assert db.get(Document,first['documentId']).last_error_code == rejected['error']
        assert db.scalar(select(func.count()).select_from(Attempt).where(Attempt.outcome == 'rejected')) == 1


def test_identity_conflict_rolls_back_created_rows(postgres_engine,store):
    body, review = source()
    cid=campaign_id(review['university_id'],review['year'],review['level'])
    pid=program_id(review['university_id'],review['level'],cid,review['source_namespace'],review['programs'][0]['source_key'])
    with postgres_engine.begin() as db:
        db.execute(insert(University).values(id=review['university_id'],name=review['university_name'],official_url=review['university_url'],provenance_url=review['url'],verified_at=datetime.fromisoformat(review['checked_at'])))
        db.execute(insert(Campaign).values(id=cid,university_id=review['university_id'],year=review['year'],level=review['level']))
        db.execute(insert(Program).values(id=pid,university_id=review['university_id'],level=review['level'],origin_campaign_id=cid,source_namespace=review['source_namespace'],source_key='conflicting-key'))
    result=import_document(postgres_engine,review,body,store)
    assert result['outcome']=='rejected' and result['error']=='catalog_identity_conflict'
    after=counts(postgres_engine)
    assert after['programs']==1 and after['program_catalog_documents']==0 and after['program_catalog_publications']==0
    assert after['program_catalog_import_attempts']==1


def test_partial_batch_failure_and_retry_isolate_universities(postgres_engine,store,tmp_path,monkeypatch):
    import app.program_catalog_import as importer
    hbody,hreview=source()
    sbody,sreview=source('sgu')
    monkeypatch.setattr(importer,'load_reviews',lambda:[hreview,sreview])
    folder=tmp_path/'originals'; folder.mkdir()
    (folder/(hreview['original_sha256']+'.html')).write_bytes(hbody)
    first=import_sources(postgres_engine,folder,store)
    assert first['atomicPerDocument'] and not first['allSourcesSucceeded']
    assert [r['outcome'] for r in first['items']]==['published','rejected']
    assert first['items'][1]['error']=='catalog_raw_unavailable'
    (folder/(sreview['original_sha256']+'.html')).write_bytes(sbody)
    second=import_sources(postgres_engine,folder,store)
    assert second['allSourcesSucceeded']
    assert [r['outcome'] for r in second['items']]==['unchanged','published']
    after=counts(postgres_engine)
    assert after['program_catalog_documents']==after['program_catalog_revisions']==2
    assert after['program_catalog_facts']==4


def test_same_keys_in_another_year_create_no_implicit_continuity(postgres_engine,store):
    body,review=source()
    first=import_document(postgres_engine,review,body,store)
    other=deepcopy(review); other['year']=2026
    other_body=body.replace(b'2027',b'2026')
    other['original_sha256']=hashlib.sha256(other_body).hexdigest()
    second=import_document(postgres_engine,other,other_body,store)
    assert first['outcome']==second['outcome']=='published'
    with Session(postgres_engine) as db:
        old=set(db.scalars(select(Fact.program_id).where(Fact.revision_id==first['revisionId'])))
        new=set(db.scalars(select(Fact.program_id).where(Fact.revision_id==second['revisionId'])))
        assert old.isdisjoint(new)


def test_reuses_existing_legacy_campaign_without_group_changes(postgres_engine,store):
    import_reviewed(postgres_engine)
    with Session(postgres_engine) as db:
        before=db.execute(select(CompetitionGroup.__table__).order_by(CompetitionGroup.id)).all()
    body,review=source('sgu')
    result=import_document(postgres_engine,review,body,store)
    assert result['outcome']=='published', result
    with Session(postgres_engine) as db:
        assert db.get(Revision,result['revisionId']).campaign_id=='sgu-2026-bachelor'
        assert db.execute(select(CompetitionGroup.__table__).order_by(CompetitionGroup.id)).all()==before


def test_programme_import_before_legacy_profiles_preserves_their_identity(postgres_engine,store):
    body,review=source('sgu')
    result=import_document(postgres_engine,review,body,store)
    assert result['outcome']=='published', result
    import_reviewed(postgres_engine)
    import_reviewed(postgres_engine)
    with Session(postgres_engine) as db:
        assert db.scalar(select(func.count()).select_from(CompetitionGroup))==2
        assert db.scalar(select(func.count()).select_from(Source))==0


def test_one_confirmed_group_can_link_multiple_programmes_without_new_identity(postgres_engine,store,monkeypatch):
    body,review=source()
    group=dict(id='synthetic-group',official_id='official-group-1',title='Synthetic combined competition',study_form='full-time',funding='budget',category='general',seats=10)
    cid=campaign_id(review['university_id'],review['year'],review['level'])
    with postgres_engine.begin() as db:
        db.execute(insert(University).values(id=review['university_id'],name=review['university_name'],official_url=review['university_url'],provenance_url=review['url'],verified_at=datetime.fromisoformat(review['checked_at'])))
        db.execute(insert(Campaign).values(id=cid,university_id=review['university_id'],year=review['year'],level=review['level']))
        db.execute(insert(CompetitionGroup).values(**group,campaign_id=cid,coverage='candidate'))
    original=EXTRACTORS[review['extractor_version']]
    def synthetic_combined(doc,scope):
        values=original(doc,scope)
        for record in values: record['groups']=[group]
        return values
    monkeypatch.setitem(EXTRACTORS,review['extractor_version'],synthetic_combined)
    for record in review['programs']: record['groups']=[group]
    result=import_document(postgres_engine,review,body,store)
    assert result['outcome']=='published'
    with Session(postgres_engine) as db:
        assert db.get(Revision,result['revisionId']).group_count==1
        assert db.scalar(select(func.count()).select_from(GroupFact))==2
        assert db.scalar(select(func.count()).select_from(CompetitionGroupProgram))==2
        assert db.scalar(select(func.count()).select_from(CompetitionGroup))==1
