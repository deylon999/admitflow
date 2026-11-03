"""Source lock + one transaction for immutable rows and the published pointer."""
from datetime import datetime, timezone

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from ..admissions import Campaign, CandidateEntry, CompetitionGroup, PublishedSnapshot, Source, SourceSnapshot
from .contracts import AdapterError, CandidateRow, ParsedList, SourceBinding
from .fetcher import FetchResult
from .registry import PRODUCTION_REGISTRY
from .storage import RawStore
from .validation import QualityPolicy, Quarantined, validate_list

QUARANTINE_CODES = frozenset({'invalid_schema','identity_mismatch','invalid_fetch_time','incomplete_list','row_count_mismatch','unconfirmed_empty_list','duplicate_candidate','duplicate_reference','invalid_official_order','future_source_time','previous_identity_mismatch','source_time_regressed','row_count_drop','capacity_drop','older_fetch','nondeterministic_parser','repeated_historical_payload','stored_snapshot_corrupt'})
STORAGE_RETRY_CODES = frozenset({'raw_lock_timeout','raw_write_failed'})
FETCH_CODES = frozenset({'invalid_url','domain_not_allowed','non_public_address','dns_unavailable','timeout','tls_error','network_error','too_many_redirects','invalid_redirect','access_denied','rate_limited','http_error','access_challenge','unsupported_encoding','unsupported_content_type','empty_response','incomplete_response','response_too_large','invalid_headers','raw_unavailable','raw_hash_mismatch','raw_size_invalid','raw_write_failed','adapter_unavailable','source_disabled','unattested_adapter','invalid_binding','invalid_format'})


def utc(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def lock_source(db, engine, source_id):
    if engine.dialect.name == 'sqlite':
        db.execute(text('BEGIN IMMEDIATE'))
    source = db.scalar(select(Source).where(Source.id==source_id).with_for_update())
    if source is None:
        raise AdapterError('unsupported_source')
    return source


def binding_from_db(db, source):
    group = db.get(CompetitionGroup,source.group_id)
    campaign = db.get(Campaign,group.campaign_id) if group else None
    if campaign is None:
        raise AdapterError('invalid_binding')
    return SourceBinding(source.id,source.group_id,campaign.year,source.url,source.domain,source.adapter_version or '',source.snapshot_kind,source.enabled)


def stored_list(db, snapshot, year):
    if snapshot.adapter_version is None or snapshot.normalized_hash is None:
        raise Quarantined('stored_snapshot_corrupt')
    rows = db.scalars(select(CandidateEntry).where(CandidateEntry.snapshot_id==snapshot.id).order_by(CandidateEntry.official_rank)).all()
    if len(rows) != snapshot.row_count or any(row.row_ref is None for row in rows):
        raise Quarantined('stored_snapshot_corrupt')
    return ParsedList(source_id=snapshot.source_id,group_id=snapshot.group_id,year=year,adapter_version=snapshot.adapter_version,kind=snapshot.kind,complete=snapshot.complete,expected_rows=snapshot.row_count,seats=snapshot.seats,source_updated_at=utc(snapshot.source_updated_at) if snapshot.source_updated_at else None,warnings=tuple(snapshot.warnings or ()),entries=tuple(CandidateRow(candidate_key=row.candidate_key,row_ref=row.row_ref,official_rank=row.official_rank,score=row.score,consent=row.consent,priority=row.priority,participation=row.participation) for row in rows))


def record_failure(engine, source_id, code, checked_at):
    code = code if code in QUARANTINE_CODES | FETCH_CODES | STORAGE_RETRY_CODES else 'internal_error'
    with Session(engine) as db:
        source = lock_source(db,engine,source_id)
        if source.last_checked_at is None or utc(source.last_checked_at) <= checked_at:
            source.last_checked_at = checked_at
            source.last_error_code = code
            db.commit()


def publish(engine, source_id: str, parsed: ParsedList, raw: FetchResult, store: RawStore, **options) -> str:
    with store.locked():
        return _publish(engine,source_id,parsed,raw,store,**options)


def _publish(engine, source_id: str, parsed: ParsedList, raw: FetchResult, store: RawStore, *, registry=PRODUCTION_REGISTRY, allow_unattested=False, policy=QualityPolicy(), expected_binding=None, lease_guard=None) -> str:
    # Raw can be orphaned after a rejected/rolled-back import; retention handles it.
    checked_at = raw.fetched_at
    with Session(engine) as db:
        source = lock_source(db,engine,source_id)
        binding = binding_from_db(db,source)
        if expected_binding is not None and binding != expected_binding:
            raise AdapterError('invalid_binding')
        adapter = registry.resolve(binding,allow_unattested=allow_unattested)
        if len(raw.body) > adapter.max_bytes:
            raise AdapterError('invalid_format')
        store.put(raw.body,raw.payload_hash)
        if lease_guard is not None:
            lease_guard(db)
        pointer = db.get(PublishedSnapshot,source_id)
        previous = db.get(SourceSnapshot,pointer.snapshot_id) if pointer else None
        previous_list = stored_list(db,previous,binding.year) if previous else None
        valid = validate_list(parsed,binding,raw.fetched_at,previous=previous_list,policy=policy)
        if previous and utc(previous.fetched_at) > raw.fetched_at:
            raise Quarantined('older_fetch')
        existing = db.scalar(select(SourceSnapshot).where(SourceSnapshot.source_id==source_id,SourceSnapshot.payload_hash==raw.payload_hash,SourceSnapshot.adapter_version==binding.adapter_version))
        if existing:
            if existing.normalized_hash != valid.normalized_hash:
                raise Quarantined('nondeterministic_parser')
            if pointer and existing.id != pointer.snapshot_id:
                raise Quarantined('repeated_historical_payload')
            snapshot_id = existing.id
        else:
            snapshot = SourceSnapshot(source_id=source_id,group_id=binding.group_id,payload_hash=raw.payload_hash,fetched_at=raw.fetched_at,source_updated_at=parsed.source_updated_at,kind=parsed.kind,row_count=len(parsed.entries),complete=True,adapter_version=binding.adapter_version,normalized_hash=valid.normalized_hash,seats=parsed.seats,warnings=list(parsed.warnings),fetched_url=raw.url,content_type=raw.content_type,charset=raw.charset)
            db.add(snapshot)
            db.flush()
            snapshot_id = snapshot.id
            db.add_all([CandidateEntry(snapshot_id=snapshot_id,**row.model_dump()) for row in parsed.entries])
            db.flush()
        if pointer:
            pointer.snapshot_id = snapshot_id
        else:
            db.add(PublishedSnapshot(source_id=source_id,snapshot_id=snapshot_id))
        source.last_checked_at = checked_at
        source.last_success_at = checked_at
        source.last_error_code = None
        from ..source_history import append_snapshot_facts
        append_snapshot_facts(db,db.get(SourceSnapshot,snapshot_id))
        from ..scenario_storage import append_source
        append_source(db,db.get(SourceSnapshot,snapshot_id),previous=previous)
        db.commit()
        return snapshot_id
