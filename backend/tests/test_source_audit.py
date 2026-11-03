from dataclasses import replace
import json
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.admissions import CandidateEntry,Source
from app.sources.audit import audit_source
from app.sources.registry import Registry
from app.sources.storage import RawStore
from test_source_lookup import lookup_context
from test_sgu_adapter import BINDING,KEY,make_adapter,response


def test_offline_audit_checks_rows_key_and_preserves_disabled_source(lookup_context,tmp_path):
    client,app=lookup_context;store=RawStore(tmp_path/'raw')
    with Session(app.state.engine) as db:
        source=db.get(Source,BINDING.source_id);source.enabled=False;db.commit()
    report=audit_source(app.state.engine,store,BINDING.source_id,registry=app.state.source_registry)
    assert report['success'] and report['checkedRows']==573 and report['checkedSnapshots']==1 and report['externalFetches']==0
    for secret in ('FIXTURE-',KEY.hex(),'candidateKey','publicCode'):assert secret not in json.dumps(report)
    with Session(app.state.engine) as db:
        assert db.get(Source,BINDING.source_id).enabled is False
        # Audit must not leave SQLite pooled connections in query-only mode.
        db.get(Source,BINDING.source_id).enabled=True;db.commit()
    wrong=Registry((make_adapter(b'w'*32),))
    result=audit_source(app.state.engine,store,BINDING.source_id,registry=wrong)
    assert not result['success'] and result['issues'][0]['code']=='normalized_hash_mismatch'
    assert audit_source(app.state.engine,store,BINDING.source_id,registry=app.state.source_registry)['success']


def test_offline_audit_refuses_raw_and_normalized_database_corruption(lookup_context,tmp_path):
    _,app=lookup_context;store=RawStore(tmp_path/'raw');raw=response()
    (store.root/raw.payload_hash).write_bytes(b'explicitly corrupted synthetic body')
    result=audit_source(app.state.engine,store,BINDING.source_id,registry=app.state.source_registry)
    assert result['issues'][0]['code']=='raw_hash_mismatch'
    (store.root/raw.payload_hash).write_bytes(raw.body)
    with Session(app.state.engine) as db:
        row=db.scalar(select(CandidateEntry).where(CandidateEntry.official_rank==1));row.consent=not row.consent;db.commit()
    result=audit_source(app.state.engine,store,BINDING.source_id,registry=app.state.source_registry)
    assert result['issues'][0]['code']=='stored_facts_mismatch'


def test_audit_limit_never_claims_unchecked_snapshots_are_valid(lookup_context,tmp_path):
    from test_source_history import publish_version
    _,app=lookup_context;publish_version(app,tmp_path,1)
    report=audit_source(app.state.engine,RawStore(tmp_path/'raw'),BINDING.source_id,registry=app.state.source_registry,limit=1)
    assert report['truncated'] and report['checkedSnapshots']==1 and not report['success']
