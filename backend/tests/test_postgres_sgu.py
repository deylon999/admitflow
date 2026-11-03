from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import timedelta
import hashlib
import os
from threading import Event

from fastapi.testclient import TestClient
import pytest

from app.config import Settings
from app.admissions import CandidateEntry,PublishedSnapshot,SourceSnapshot
from app.jobs import enqueue
from app.main import create_app
from app.sources.registry import Registry
from app.sources.storage import RawStore
from app.sources.publishing import publish
from app.worker import run_once
from native_support import postgres_engine
from sgu_helpers import seed_sgu
from test_api import HEADERS
from test_sgu_adapter import BINDING,KEY,make_adapter,response
from test_sgu_worker import test_real_format_worker_success_then_bad_page_retains_last_good
from test_pilot_registration import (
    test_registration_is_explicit_disabled_and_idempotent,
    test_enable_requires_attested_key_and_conflicting_metadata_is_not_overwritten,
)
from test_source_lookup import (
    test_lookup_requires_guest_and_never_creates_a_subscription,
    test_invalid_lookup_does_not_echo_code_or_accept_other_sources,
)
from test_subscriptions import (
    test_repeated_confirmation_saves_once_and_other_owner_cannot_use_it,
    test_manual_and_archive_share_twenty_limit_under_concurrent_writes,
    test_stale_unconsumed_confirmation_refuses_but_successful_replay_ignores_expiry,
    test_guest_reset_removes_subscription_assessment_and_operation_payload,
    test_expiry_hides_private_rows_and_cleanup_keeps_shared_archive,
)
from sqlalchemy import func,select
from sqlalchemy.orm import Session

pytestmark=pytest.mark.postgres


@pytest.fixture
def source_engine(postgres_engine):return postgres_engine


@pytest.fixture
def lookup_context(source_engine,tmp_path,monkeypatch):
    from app.sources.pilots import register_sgu
    monkeypatch.setenv('SOURCE_IDENTITY_KEY',KEY.hex())
    app=create_app(Settings(database_url=source_engine.url.render_as_string(hide_password=False),auto_create_schema=False))
    with TestClient(app) as client:
        register_sgu(source_engine,enable=True,registry=app.state.source_registry)
        raw=response();parsed=app.state.source_registry.resolve(BINDING).parse(raw,BINDING)
        publish(source_engine,BINDING.source_id,parsed,raw,RawStore(tmp_path/'raw'),registry=app.state.source_registry)
        yield client,app


def test_blocked_real_source_worker_does_not_block_manual_api(source_engine,tmp_path):
    seed_sgu(source_engine);raw=response();enqueue(source_engine,BINDING.source_id,now=raw.fetched_at)
    started,release=Event(),Event()
    def fetch(*_,**__):
        started.set()
        if not release.wait(timeout=10):raise RuntimeError('Fetch gate timed out')
        return raw
    app=create_app(Settings(database_url=source_engine.url.render_as_string(hide_password=False),auto_create_schema=False))
    with ThreadPoolExecutor(max_workers=1) as pool:
        future=pool.submit(run_once,source_engine,RawStore(tmp_path/'raw'),registry=Registry((make_adapter(KEY),)),fetch=fetch,now=lambda:raw.fetched_at)
        try:
            assert started.wait(timeout=5)
            with TestClient(app) as client:
                assert client.get('/api/health').status_code==200
                assert client.post('/api/v1/session',headers=HEADERS).status_code==204
                assert client.get('/api/v1/watches').json()==[]
                assert client.get('/api/v1/universities').status_code==200
        finally:release.set()
        assert future.result(timeout=10)['state']=='success'


def test_real573_row_repeat_and_failed_insert_are_atomic(source_engine,tmp_path,monkeypatch):
    seed_sgu(source_engine);raw=response();adapter=make_adapter(KEY);registry=Registry((adapter,));store=RawStore(tmp_path/'raw')
    parsed=adapter.parse(raw,BINDING)
    def send(_):return publish(source_engine,BINDING.source_id,parsed,raw,store,registry=registry)
    with ThreadPoolExecutor(max_workers=4) as pool:ids=list(pool.map(send,range(8)))
    assert len(set(ids))==1
    original=Session.flush
    def fail_rows(db,*args,**kwargs):
        if any(isinstance(row,CandidateEntry) for row in db.new):raise RuntimeError('Injected row-write failure')
        return original(db,*args,**kwargs)
    body=b'<!-- synthetic template-only fault injection -->\n'+raw.body
    changed=replace(raw,body=body,payload_hash=hashlib.sha256(body).hexdigest(),fetched_at=raw.fetched_at+timedelta(minutes=1))
    with monkeypatch.context() as patch:
        patch.setattr(Session,'flush',fail_rows)
        with pytest.raises(RuntimeError,match='Injected'):
            publish(source_engine,BINDING.source_id,adapter.parse(changed,BINDING),changed,store,registry=registry)
    with Session(source_engine) as db:
        assert db.get(PublishedSnapshot,BINDING.source_id).snapshot_id==ids[0]
        assert db.scalar(select(func.count()).select_from(SourceSnapshot))==1
        assert db.scalar(select(func.count()).select_from(CandidateEntry))==573
    assert store.read(raw.payload_hash)==raw.body


def test_real_archive_worker_crash_after_commit_replays_without_another_snapshot(source_engine,tmp_path,monkeypatch):
    seed_sgu(source_engine);raw=response();enqueue(source_engine,BINDING.source_id,now=raw.fetched_at)
    registry=Registry((make_adapter(KEY),));store=RawStore(tmp_path/'raw')
    def crash(*_,**__):raise SystemExit('Injected process death after commit')
    with monkeypatch.context() as patch:
        patch.setattr('app.worker.complete',crash)
        with pytest.raises(SystemExit):
            run_once(source_engine,store,registry=registry,fetch=lambda *_,**__:raw,now=lambda:raw.fetched_at)
    later=raw.fetched_at+timedelta(seconds=121)
    assert run_once(source_engine,store,registry=registry,fetch=lambda *_,**__:replace(raw,fetched_at=later),now=lambda:later)['state']=='success'
    with Session(source_engine) as db:
        assert db.scalar(select(func.count()).select_from(SourceSnapshot))==1
        assert db.scalar(select(func.count()).select_from(CandidateEntry))==573
        snapshot=db.scalar(select(SourceSnapshot))
        assert snapshot.source_updated_at is None and snapshot.kind=='archive' and snapshot.adapter_version==BINDING.adapter_version


def test_raw_retention_keeps_all_referenced_archive_versions(source_engine,tmp_path):
    from app.sources.retention import cleanup_raw
    seed_sgu(source_engine);raw=response();adapter=make_adapter(KEY);registry=Registry((adapter,));store=RawStore(tmp_path/'raw')
    publish(source_engine,BINDING.source_id,adapter.parse(raw,BINDING),raw,store,registry=registry)
    body=b'<!-- synthetic template-only retention version -->\n'+raw.body
    second=replace(raw,body=body,payload_hash=hashlib.sha256(body).hexdigest(),fetched_at=raw.fetched_at+timedelta(minutes=1))
    publish(source_engine,BINDING.source_id,adapter.parse(second,BINDING),second,store,registry=registry)
    orphan=store.put(b'expired synthetic orphan')
    for digest in (raw.payload_hash,second.payload_hash,orphan):
        os.utime(store.root/digest,(raw.fetched_at.timestamp()-10*86400,)*2)
    preview=cleanup_raw(source_engine,store,now=raw.fetched_at)
    assert preview['candidates']==1 and preview['deleted']==0 and preview['retained']==2
    result=cleanup_raw(source_engine,store,now=raw.fetched_at,apply=True)
    assert result['deleted']==1 and not (store.root/orphan).exists()
    assert store.read(raw.payload_hash)==raw.body and store.read(second.payload_hash)==second.body

from test_source_lookup import test_lookup_budget_is_shared_by_requests_resets_and_does_not_store_codes

from test_source_deletion import test_archive_delete_is_private_cascading_and_tombstones_replays, test_delete_racing_with_success_replay_cannot_resurrect

from test_source_history import test_archive_history_is_immutable_paginated_private_and_idempotent, test_history_failure_rolls_back_publication_and_pointer

from test_source_history import test_synthetic_changed_facts_keep_the_confirmation_unchanged

from test_source_recovery import test_real_format_failure_quarantine_recovery_retains_history
from test_source_recovery import test_synthetic_quality_quarantine_then_recovery_keeps_both_outcomes
from test_archive_export import test_archive_export_is_private_bounded_factual_and_not_a_bearer_backup
from test_subscriptions import test_batch_archive_cards_keep_twenty_identities_and_explicit_missing_row
from test_source_audit import test_offline_audit_checks_rows_key_and_preserves_disabled_source, test_offline_audit_refuses_raw_and_normalized_database_corruption
from test_source_audit import test_audit_limit_never_claims_unchecked_snapshots_are_valid
from test_source_security import test_guest_removed_during_lookup_never_returns_private_facts, test_guest_deadline_crossed_during_lookup_does_not_issue_expired_confirmation
from test_source_history import test_processing_time_is_separate_from_archive_fetch_and_retry_keeps_it
from test_scenario_storage import test_versioned_scenario_reproduces_diff_and_history_without_mutation, test_assessment_failure_rolls_back_all_publication_and_preserves_previous, test_explicit_policy_backfills_existing_subscription_and_declines_paid_source
