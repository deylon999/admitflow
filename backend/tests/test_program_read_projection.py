"""Native PostgreSQL publication/read-index equivalence, no real source evidence."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
import os
from pathlib import Path

from alembic import command
from alembic.config import Config
import pytest
from sqlalchemy import delete, insert, select, update
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session

from app.catalog import product_catalog as facade, read_projection
from app.catalog.program_catalog_models import ProgramCatalogDocument as Document, ProgramCatalogRevision as Revision, ProgramCatalogFact as Fact, ProgramCatalogPublication as Publication, ProgramCatalogReadFact as ReadFact, ProgramCatalogReadScope as Scope
from app.catalog.program_catalog_import import import_document
from app.catalog.catalog_import import import_reviewed
from app.sources.storage import RawStore
from native_support import postgres_engine  # noqa: F401
from pg_support import isolated_postgres
from test_program_catalog_import import source, store  # noqa: F401
from test_program_publication_api import changed_source

pytestmark=pytest.mark.postgres


def publish(engine,store):
    body,review=source()
    result=import_document(engine,review,body,store)
    assert result['outcome']=='published',result
    return body,review,result


def values(engine):
    with Session(engine) as db:
        return sorted((r.revision_id,r.program_id,r.in_scope,r.eligible) for r in db.scalars(select(ReadFact)))


def page(engine):
    with Session(engine) as db:
        return facade.program_page(db).model_dump(mode='json')


def clone(engine,rid):
    with Session(engine) as db:
        r=db.get(Revision,rid)
        revision={c.name:getattr(r,c.name) for c in Revision.__table__.columns}
        facts=[{c.name:getattr(f,c.name) for c in Fact.__table__.columns} for f in db.scalars(select(Fact).where(Fact.revision_id==rid))]
    with engine.begin() as db:
        db.execute(insert(Document).values(id='rival-document',campaign_id=revision['campaign_id'],source_namespace='synthetic-read-rival'))
        db.execute(insert(Revision).values(**(revision|dict(id='rival-revision',document_id='rival-document'))))
        db.execute(insert(Fact),[f|dict(revision_id='rival-revision') for f in facts])
    return revision['document_id']


def test_projection_matches_source_and_is_actually_used(postgres_engine,store,monkeypatch):
    publish(postgres_engine,store)
    with Session(postgres_engine) as db:
        assert db.get(Scope,1).scope_hash==read_projection.policy()['scope_hash']
        assert read_projection.statement(db) is not None
        assert facade.program_page(db).model_dump()==facade.source_program_page(db).model_dump()
    assert len(values(postgres_engine))==2 and all(r[3] for r in values(postgres_engine))
    monkeypatch.setattr(facade,'source_program_page',lambda *a,**kw:pytest.fail('unexpected slow fallback'))
    assert page(postgres_engine)['total']==2


def test_revision_switch_and_transaction_failure_preserve_cache(postgres_engine,store):
    body,review,_=publish(postgres_engine,store)
    before=values(postgres_engine)
    new_body,new_review=changed_source(body,review)
    assert import_document(postgres_engine,new_review,new_body,store)['outcome']=='published'
    assert {r[1] for r in values(postgres_engine)}=={r[1] for r in before}
    assert {r[0] for r in values(postgres_engine)}!={r[0] for r in before}
    snapshot=values(postgres_engine)
    with pytest.raises(RuntimeError):
        with postgres_engine.begin() as db:
            db.execute(delete(Publication))
            assert db.scalar(select(ReadFact.program_id)) is None
            raise RuntimeError('synthetic rollback')
    assert values(postgres_engine)==snapshot
    assert import_document(postgres_engine,review,body,store)['outcome']=='rejected'
    assert values(postgres_engine)==snapshot


def test_unpublish_reopens_both_conflict_keys(postgres_engine,store):
    _,_,result=publish(postgres_engine,store)
    clone(postgres_engine,result['revisionId'])
    with postgres_engine.begin() as db:
        db.execute(insert(Publication).values(document_id='rival-document',revision_id='rival-revision'))
    assert len(values(postgres_engine))==4 and not any(r[3] for r in values(postgres_engine))
    assert page(postgres_engine)['total']==0
    with postgres_engine.begin() as db:
        db.execute(delete(Publication).where(Publication.document_id=='rival-document'))
    assert len(values(postgres_engine))==2 and all(r[3] for r in values(postgres_engine))
    assert page(postgres_engine)['total']==2


def test_policy_changes_are_atomic_and_mismatch_uses_exact_fallback(postgres_engine,store):
    publish(postgres_engine,store)
    before=page(postgres_engine)
    policy=deepcopy(read_projection.policy())
    policy['known_ids']=['sgu-saratov']
    signature='known:\n'+'\n'.join(policy['known_ids'])+'\nreserved:\n'+'\n'.join(policy['reserved_ids'])
    policy['scope_hash']=hashlib.sha256(signature.encode()).hexdigest()
    with postgres_engine.begin() as db:
        db.execute(update(Scope).where(Scope.id==1).values(**policy))
    assert not any(r[2] or r[3] for r in values(postgres_engine))
    with Session(postgres_engine) as db:
        assert read_projection.statement(db) is None
    assert page(postgres_engine)==before
    read_projection.refresh_policy(postgres_engine)
    assert all(r[2] and r[3] for r in values(postgres_engine))
    assert page(postgres_engine)==before


@pytest.mark.parametrize('operation',['update','delete','insert'])
def test_direct_mutation_of_derived_rows_is_rejected(postgres_engine,store,operation):
    publish(postgres_engine,store)
    before=values(postgres_engine)
    with pytest.raises(IntegrityError):
        with postgres_engine.begin() as db:
            if operation=='update':db.execute(update(ReadFact).values(eligible=False))
            elif operation=='delete':db.execute(delete(ReadFact))
            else:
                row=db.execute(select(ReadFact.__table__)).mappings().first()
                db.execute(insert(ReadFact).values(**(dict(row)|dict(revision_id='synthetic-invalid'))))
    assert values(postgres_engine)==before


def test_scope_cannot_be_removed_or_given_false_fingerprint(postgres_engine):
    for mutation in [delete(Scope),update(Scope).values(scope_hash='0'*64)]:
        with pytest.raises(DBAPIError):
            with postgres_engine.begin() as db:db.execute(mutation)
    with Session(postgres_engine) as db:
        assert db.get(Scope,1).scope_hash==read_projection.policy()['scope_hash']


def test_scope_cannot_forge_a_policy_by_joining_ids_with_newlines(postgres_engine):
    expected=read_projection.policy()
    with pytest.raises(DBAPIError):
        with postgres_engine.begin() as db:
            db.execute(update(Scope).values(known_ids=['\n'.join(expected['known_ids'])]))
    with Session(postgres_engine) as db:
        assert db.get(Scope,1).scope_hash==expected['scope_hash']


def test_concurrent_publications_do_not_miss_each_other(postgres_engine,store):
    _,_,result=publish(postgres_engine,store)
    original=clone(postgres_engine,result['revisionId'])
    with postgres_engine.begin() as db:db.execute(delete(Publication))
    import threading
    barrier=threading.Barrier(2)
    def writer(pair):
        with postgres_engine.begin() as db:
            barrier.wait(timeout=10)
            db.execute(insert(Publication).values(document_id=pair[0],revision_id=pair[1]))
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(writer,[(original,result['revisionId']),('rival-document','rival-revision')]))
    assert len(values(postgres_engine))==4 and not any(r[3] for r in values(postgres_engine))
    assert page(postgres_engine)['total']==0


def test_repeatable_read_writer_cannot_apply_an_old_global_snapshot(postgres_engine,store):
    _,_,result=publish(postgres_engine,store)
    original=clone(postgres_engine,result['revisionId'])
    with postgres_engine.begin() as db:db.execute(delete(Publication))
    with postgres_engine.connect().execution_options(isolation_level='REPEATABLE READ') as stale:
        stale.execute(select(Scope.epoch))
        with postgres_engine.begin() as db:
            db.execute(insert(Publication).values(document_id=original,revision_id=result['revisionId']))
        with pytest.raises(DBAPIError) as error:
            stale.execute(insert(Publication).values(document_id='rival-document',revision_id='rival-revision'))
        assert error.value.orig.sqlstate=='40001'
        stale.rollback()
    assert len(values(postgres_engine))==2 and all(r[3] for r in values(postgres_engine))


def test_populated_0014_upgrade_and_downgrade_keep_source_history(postgres_engine,tmp_path):
    config=Config(str(Path(__file__).resolve().parents[1]/'alembic.ini'))
    with isolated_postgres(os.environ['TEST_DATABASE_URL']) as engine:
        with engine.connect() as connection:
            config.attributes['connection']=connection
            command.upgrade(config,'0014')
        import_reviewed(engine)
        _,_,result=publish(engine,RawStore(tmp_path/'migration-raw'))
        with engine.connect() as connection:
            config.attributes['connection']=connection
            command.upgrade(config,'0015')
            command.check(config)
        assert len(values(engine))==2 and all(r[3] for r in values(engine))
        with engine.connect() as connection:
            config.attributes['connection']=connection
            command.downgrade(config,'0014')
            assert connection.scalar(select(Publication.revision_id))==result['revisionId']
            connection.rollback()
            command.upgrade(config,'0015')
        assert len(values(engine))==2 and all(r[3] for r in values(engine))
