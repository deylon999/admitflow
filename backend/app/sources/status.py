"""Public source diagnostics contain no candidates or raw payloads."""
from datetime import datetime, timezone
from urllib.parse import urlsplit

from sqlalchemy.orm import Session

from ..admissions import PublishedSnapshot, Source, SourceSnapshot
from ..jobs import SourceJob
from .contracts import AdapterError
from .publishing import QUARANTINE_CODES, binding_from_db, utc
from .registry import PRODUCTION_REGISTRY


def source_status(db: Session, source_id: str, *, now=None, registry=PRODUCTION_REGISTRY, freshness_seconds=1800):
    now = now or datetime.now(timezone.utc)
    if not 30 <= freshness_seconds <= 86400:
        raise ValueError('invalid_freshness_policy')
    source = db.get(Source,source_id)
    if source is None:
        return None
    binding = binding_from_db(db,source)
    pointer = db.get(PublishedSnapshot,source_id)
    snapshot = db.get(SourceSnapshot,pointer.snapshot_id) if pointer else None
    job = db.get(SourceJob,source_id)
    worker_state = job.state if job else 'unknown'
    if job and job.state == 'running' and utc(job.lease_until) <= now:
        worker_state = 'expired'
    try:
        registry.resolve(binding)
        available=True
    except AdapterError:
        available=False
    kind = snapshot.kind if snapshot else source.snapshot_kind
    # Archive classification also checks the season, independently of success time.
    if binding.year < now.year or source.snapshot_kind == 'archive':
        kind='archive'
    checked=utc(source.last_checked_at) if source.last_checked_at else None
    success=utc(source.last_success_at) if source.last_success_at else None
    if not source.enabled:
        state='disabled'
    elif source.last_error_code:
        state='quarantined' if source.last_error_code in QUARANTINE_CODES else 'source_error'
    elif worker_state in ('failed','expired'):
        state='source_error'
    elif not snapshot:
        state='unknown'
    elif kind == 'archive':
        state='archived'
    elif not available or (snapshot and snapshot.adapter_version != binding.adapter_version):
        state='unsupported'
    elif not snapshot.complete or not snapshot.normalized_hash or not success or (success-now).total_seconds() > 300:
        state='unknown'
    else:
        state='fresh' if (now-success).total_seconds() <= freshness_seconds else 'stale'
    try:
        url=urlsplit(source.url)
        safe_url = source.url if url.scheme=='https' and not url.username and not url.password else None
    except ValueError:
        safe_url=None
    return dict(sourceId=source.id,groupId=source.group_id,season=binding.year,state=state,dataKind=kind,workerState=worker_state,enabled=source.enabled,adapterAvailable=available,assessmentAvailable=False,sourceUrl=safe_url,adapterVersion=snapshot.adapter_version if snapshot else None,publishedSnapshotId=snapshot.id if snapshot else None,lastCheckedAt=checked,lastSuccessfulCheckAt=success,fetchedAt=utc(snapshot.fetched_at) if snapshot else None,sourceUpdatedAt=utc(snapshot.source_updated_at) if snapshot and snapshot.source_updated_at else None,freshnessSeconds=freshness_seconds)
