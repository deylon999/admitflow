"""Verify publication boundaries on migrated PostgreSQL with synthetic archives."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Event

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.admissions import CandidateEntry, PublishedSnapshot, SourceSnapshot
from app.sources.storage import RawStore
from native_support import postgres_engine
from source_helpers import NOW, raw, seed_source
from test_publishing import (
    publish_sample,
    test_atomic_repeat_concurrency_and_new_parser_version,
    test_rejected_or_failed_write_preserves_latest_and_history,
    test_reinterpreting_same_raw_with_same_version_is_quarantined,
)
from test_worker import (
    test_synthetic_worker_success_then_quarantine_preserves_latest,
    test_crash_after_publication_replays_without_second_snapshot,
    test_parser_exception_text_is_not_saved_or_returned,
)

pytestmark = pytest.mark.postgres


@pytest.fixture
def source_engine(postgres_engine):
    return postgres_engine


def test_reader_sees_only_complete_snapshots_during_uncommitted_publication(source_engine, tmp_path, monkeypatch):
    seed_source(source_engine)
    store = RawStore(tmp_path / 'raw')
    first = publish_sample(source_engine, store)
    inserted, release = Event(), Event()
    original = Session.flush

    def pause_after_rows(db, *args, **kwargs):
        has_rows = any(isinstance(row, CandidateEntry) for row in db.new)
        result = original(db, *args, **kwargs)
        if has_rows:
            inserted.set()
            if not release.wait(timeout=10):
                raise RuntimeError('Publication gate timed out')
        return result

    monkeypatch.setattr(Session, 'flush', pause_after_rows)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(publish_sample, source_engine, store, response=raw(b'next complete payload', NOW + timedelta(minutes=1)))
        try:
            assert inserted.wait(timeout=5)
            # Inserts have reached PostgreSQL, but the transaction is not committed.
            with Session(source_engine) as db:
                assert db.get(PublishedSnapshot, 'source-1').snapshot_id == first
                assert db.scalar(select(func.count()).select_from(SourceSnapshot)) == 1
                assert db.scalar(select(func.count()).select_from(CandidateEntry)) == 3
        finally:
            release.set()
        second = future.result(timeout=5)
    with Session(source_engine) as db:
        assert second != first
        assert db.get(PublishedSnapshot, 'source-1').snapshot_id == second
        snapshots = db.scalars(select(SourceSnapshot)).all()
        assert len(snapshots) == 2
        assert db.scalar(select(func.count()).select_from(CandidateEntry)) == 6
        for snapshot in snapshots:
            assert store.read(snapshot.payload_hash)
