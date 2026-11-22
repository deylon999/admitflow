"""Operator import of closed reviewed programme documents, atomic per source.

No HTTP write route, applicant parsing, source activation or implicit contests.
"""
import argparse
import hashlib
from datetime import date, datetime, timezone
import json
from pathlib import Path
import re
from uuid import uuid5

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .admissions import Campaign, CampaignProgram, CompetitionGroup, CompetitionGroupProgram, Program, University
from .catalog_identity import NAMESPACE_V1, campaign_id, identity_text, program_id
from .catalog_import import reviewed_profiles
from .catalog_lock import lock_catalog
from .national_catalog import load_catalog
from .program_catalog_models import (ProgramCatalogDocument as Document, ProgramCatalogRevision as Revision,
    ProgramCatalogFact as Fact, ProgramCatalogGroupFact as GroupFact, ProgramCatalogPublication as Publication,
    ProgramCatalogImportAttempt as Attempt)
from .program_catalog_review import canonical_hash, extract_reviewed, load_reviews
from .sources.storage import StorageError
from .sources.table_profiles import PROFILES


def scoped_id(kind, *parts):
    return str(uuid5(NAMESPACE_V1, json.dumps(['admitflow-catalog-v1', kind, *parts], ensure_ascii=False, separators=(',', ':'))))


def _timestamp(value):
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError('catalog_invalid_timestamp')
    return parsed.astimezone(timezone.utc)


def _ensure(db, model, identifier, fields, **defaults):
    row = db.get(model, identifier)
    if row is None:
        row = model(id=identifier, **fields, **defaults)
        db.add(row)
        db.flush()
    if any(getattr(row, k) != v for k, v in fields.items()):
        raise ValueError('catalog_identity_conflict')
    return row


def _validate(review, body):
    if review.get('verification_status') != 'verified':
        raise ValueError('catalog_unreviewed_document')
    identity_text(review['document_type'], 40)
    if body is None:
        raise ValueError('catalog_raw_unavailable')
    if review['completeness'] != 'partial':
        # Current extractors prove a selected scope, never a whole university.
        raise ValueError('catalog_unsupported_completeness')
    if not re.fullmatch(r'[a-f0-9]{64}', review['original_sha256']):
        raise ValueError('catalog_invalid_original_hash')
    _timestamp(review['fetched_at'])
    if _timestamp(review['checked_at']) < _timestamp(review['fetched_at']):
        raise ValueError('catalog_invalid_timestamp')
    identity_text(review['source_namespace'], 160)
    records = extract_reviewed(body, review)
    if not records or len({r['source_key'] for r in records}) != len(records):
        raise ValueError('catalog_incomplete_document')
    for record in records:
        identity_text(record['source_key'], 300)
        identity_text(record['title'], 300)
        for field, maximum in [('study_form',40), ('funding',40), ('category',80)]:
            if record[field] is not None:
                identity_text(record[field], maximum)
        if record['code'] is not None and not re.fullmatch(r'\d{2}\.\d{2}\.\d{2}', record['code']):
            raise ValueError('catalog_invalid_program_code')
        if record['seats'] is not None and (type(record['seats']) is not int or record['seats'] < 0):
            raise ValueError('catalog_invalid_places')
        totals = record['admission_totals']
        if totals is not None and (set(totals) != {'budget_total','paid_total','target_quota','special_quota','separate_quota'}
                or any(v is not None and (type(v) is not int or v < 0) for v in totals.values())):
            raise ValueError('catalog_invalid_places')
        if len({g['id'] for g in record['groups']}) != len(record['groups']):
            raise ValueError('catalog_duplicate_group')
    return records


def _scope(db, review):
    catalog = load_catalog()
    org = next((u for u in catalog.institutions if u.id == review['university_id']), None)
    if not org or org.is_branch or (org.name, org.official_url, org.region) != (review['university_name'], review['university_url'], review['region']):
        raise ValueError('catalog_university_scope_mismatch')
    university = db.get(University, org.id)
    known_profiles = (*reviewed_profiles(), *(p for p in PROFILES.values() if p.proof is not None))
    legacy = [p for p in known_profiles if dict(p.catalog)['university_id'] == org.id]
    allowed_pairs = {(org.name, org.official_url)} | {(dict(p.catalog)['university_name'], dict(p.catalog)['university_url']) for p in legacy}
    if university and (university.name, university.official_url) not in allowed_pairs:
        raise ValueError('catalog_university_identity_conflict')
    if university is None:
        # Reuse explicitly reviewed legacy identity spelling/URL in either import
        # order; no URL normalization, fuzzy name match or mutation of old rows.
        metadata = dict(legacy[0].catalog) if legacy else None
        university = _ensure(db, University, org.id,
            dict(name=metadata['university_name'] if metadata else org.name,
                 official_url=metadata['university_url'] if metadata else org.official_url),
            region=org.region, provenance_url=legacy[0].url if legacy else org.provenance_url,
            verified_at=legacy[0].proof.verified_at if legacy else catalog.captured_at)
    campaign = db.scalar(select(Campaign).where(Campaign.university_id == org.id, Campaign.year == review['year'], Campaign.level == review['level']))
    if campaign is None:
        known_campaign_ids = {dict(p.catalog)['campaign_id'] for p in legacy if p.year == review['year'] and dict(p.catalog)['level'] == review['level']}
        if len(known_campaign_ids) > 1:
            raise ValueError('catalog_campaign_identity_ambiguous')
        identifier = next(iter(known_campaign_ids)) if known_campaign_ids else campaign_id(org.id, review['year'], review['level'])
        campaign = _ensure(db, Campaign, identifier,
            dict(university_id=org.id, year=review['year'], level=review['level']))
    document = db.scalar(select(Document).where(Document.campaign_id == campaign.id, Document.source_namespace == review['source_namespace']))
    if document is None:
        document = _ensure(db, Document, scoped_id('program-document', org.id, review['year'], review['level'], review['source_namespace']),
            dict(campaign_id=campaign.id, source_namespace=review['source_namespace']))
    return university, campaign, document, org


def _program(db, campaign, review, record):
    candidates = db.scalars(select(Program).join(CampaignProgram, Program.id == CampaignProgram.program_id).where(
        CampaignProgram.campaign_id == campaign.id, Program.source_namespace == review['source_namespace'], Program.source_key == record['source_key'])).all()
    if len(candidates) > 1:
        raise ValueError('catalog_program_identity_ambiguous')
    if candidates:
        return candidates[0]
    fields = dict(university_id=campaign.university_id, level=campaign.level, origin_campaign_id=campaign.id,
                  source_namespace=review['source_namespace'], source_key=record['source_key'])
    existing = db.scalar(select(Program).where(Program.origin_campaign_id == campaign.id,
        Program.source_namespace == review['source_namespace'], Program.source_key == record['source_key']))
    identifier = existing.id if existing else program_id(campaign.university_id, campaign.level, campaign.id, review['source_namespace'], record['source_key'])
    program = _ensure(db, Program, identifier, fields)
    db.add(CampaignProgram(program_id=program.id, campaign_id=campaign.id, university_id=campaign.university_id, level=campaign.level))
    db.flush()
    return program


def _group_links(db, campaign, program, records):
    for value in records:
        group = db.get(CompetitionGroup, value['id'])
        fields = ('official_id', 'title', 'study_form', 'funding', 'category', 'seats')
        if group is None or group.campaign_id != campaign.id or any(getattr(group, k) != value[k] for k in fields):
            raise ValueError('catalog_group_identity_conflict')
        key = (group.id, program.id)
        if db.get(CompetitionGroupProgram, key) is None:
            db.add(CompetitionGroupProgram(group_id=group.id, program_id=program.id, campaign_id=campaign.id))
    db.flush()


def _rejected(engine, review, body, document_id, now, stage, error):
    code = str(error) if isinstance(error, ValueError) and re.fullmatch(r'catalog_[a-z_]+', str(error)) else 'catalog_import_failed'
    if isinstance(error, StorageError):
        code = 'catalog_' + error.code
    with Session(engine) as db:
        lock_catalog(db, engine)
        document = db.get(Document, document_id)
        if document:
            document.last_checked_at = now
            document.last_error_code = code
        db.add(Attempt(document_id=document_id, attempted_at=now, stage=stage, outcome='rejected', error_code=code,
            original_sha256=hashlib.sha256(body).hexdigest() if isinstance(body, bytes) and len(body) <= 5*1024*1024 else None))
        db.commit()
    return dict(documentId=document_id, outcome='rejected', stage=stage, error=code)


def import_document(engine, review, body, raw_store):
    """Internal trusted-review entry point; CLI only selects shipped review keys."""
    try:
        # Match snapshot publication/backup/retention lock order. Referenced raw
        # cannot be collected between writing it and committing its revision.
        with raw_store.locked():
            return _import_document_locked(engine, review, body, raw_store)
    except StorageError as error:
        document_id = scoped_id('program-document', review['university_id'], review['year'], review['level'], review['source_namespace'])
        return _rejected(engine, review, body, document_id, datetime.now(timezone.utc), 'validation', error)


def _import_document_locked(engine, review, body, raw_store):
    now = datetime.now(timezone.utc)
    document_id = scoped_id('program-document', review['university_id'], review['year'], review['level'], review['source_namespace'])
    stage = 'validation'
    try:
        records = _validate(review, body)
        raw_store.put(body, expected_hash=review['original_sha256'])
        normalized = canonical_hash(records)
        review_hash = canonical_hash(review)
        with Session(engine) as db:
            lock_catalog(db, engine)
            stage = 'identity'
            university, campaign, document, org = _scope(db, review)
            document_id = document.id
            pointer = db.get(Publication, document.id)
            previous = db.get(Revision, pointer.revision_id) if pointer else None
            existing = db.scalar(select(Revision).where(Revision.document_id == document.id,
                Revision.original_sha256 == review['original_sha256'], Revision.extractor_version == review['extractor_version'], Revision.review_sha256 == review_hash))
            if existing:
                if existing.normalized_sha256 != normalized:
                    raise ValueError('catalog_nondeterministic_extractor')
                if not pointer or pointer.revision_id != existing.id:
                    raise ValueError('catalog_historical_revision_replay')
                revision = existing
                outcome = 'unchanged'
            else:
                if previous and _timestamp(review['checked_at']) < previous.checked_at:
                    raise ValueError('catalog_older_review')
                identities = [(r, _program(db, campaign, review, r)) for r in records]
                previous_ids = set(db.scalars(select(Fact.program_id).where(Fact.revision_id == previous.id))) if previous else set()
                if not previous_ids <= {p.id for _, p in identities}:
                    raise ValueError('catalog_program_set_drop')
                revision = Revision(id=scoped_id('program-revision', document.id, review['original_sha256'], review['extractor_version'], review_hash),
                    document_id=document.id, campaign_id=campaign.id, original_url=review['url'], final_url=review['final_url'],
                    content_type=review['content_type'], publication_date=date.fromisoformat(review['publication_date']) if review['publication_date'] else None,
                    document_type=review['document_type'], verification_status='verified',
                    fetched_at=_timestamp(review['fetched_at']), checked_at=_timestamp(review['checked_at']), original_sha256=review['original_sha256'],
                    extractor_version=review['extractor_version'], review_sha256=review_hash, normalized_sha256=normalized,
                    completeness=review['completeness'], program_count=len(records), group_count=len({g['id'] for r in records for g in r['groups']}), university_name=university.name)
                db.add(revision)
                db.flush()
                for record, program in identities:
                    _group_links(db, campaign, program, record['groups'])
                    fact_fields = {k:record[k] for k in ('source_key','title','code','study_form','funding','category','seats','admission_totals')}
                    db.add(Fact(revision_id=revision.id, program_id=program.id, campaign_id=campaign.id,
                        public_id=scoped_id('program-scope', program.id, campaign.id), **fact_fields,
                        evidence=dict(selection=record['source_key'], originalSha256=review['original_sha256'],
                            organizationCatalogSha256=load_catalog().sha256, organizationCatalogUrl=org.provenance_url,
                            universityRowOriginUrl=university.provenance_url),
                        search_text=f'{record["title"]} {record["code"] or ""} {university.name}'.casefold(), sort_text=record['title'].casefold()))
                    db.flush()
                    db.add_all([GroupFact(revision_id=revision.id, program_id=program.id, group_id=g['id'], campaign_id=campaign.id, facts=g) for g in record['groups']])
                    db.flush()
                stage = 'publication'
                if pointer:
                    pointer.revision_id = revision.id
                else:
                    db.add(Publication(document_id=document.id, revision_id=revision.id))
                db.flush()
                outcome = 'published'
            document.last_checked_at = now
            document.last_error_code = None
            db.add(Attempt(document_id=document.id, attempted_at=now, stage='publication', outcome=outcome,
                original_sha256=review['original_sha256'], revision_id=revision.id))
            revision_id = revision.id
            db.commit()
        return dict(documentId=document_id, revisionId=revision_id, outcome=outcome, programs=len(records), completeUniversityCatalog=False)
    except (ValueError, KeyError, TypeError, SQLAlchemyError, StorageError) as error:
        return _rejected(engine, review, body, document_id, now, stage, error)


def import_sources(engine, raw_directory, raw_store, *, keys=None):
    reviews = load_reviews()
    if keys is not None:
        if not keys or len(set(keys)) != len(keys) or not set(keys) <= {r['key'] for r in reviews}:
            raise ValueError('catalog_unknown_review_key')
        reviews = [r for r in reviews if r['key'] in keys]
    results = [import_document(engine, review, read_original(raw_directory, review), raw_store) for review in reviews]
    return dict(atomicPerDocument=True, allSourcesSucceeded=all(r['outcome'] != 'rejected' for r in results), items=results)


def read_original(raw_directory, review):
    path = Path(raw_directory) / (review['original_sha256'] + '.html')
    try:
        if path.is_file() and not path.is_symlink():
            with path.open('rb') as file:
                return file.read(5*1024*1024+1)
    except OSError:
        # The caller journals an unavailable document and continues the batch.
        pass
    return None


def require_import_schema(engine):
    from .migrations import schema_heads
    from sqlalchemy import text
    if engine.dialect.name != 'postgresql':
        raise ValueError('catalog_import_requires_postgresql')
    try:
        with engine.connect() as connection:
            revisions = set(connection.scalars(text('SELECT version_num FROM alembic_version')))
        if revisions != schema_heads():
            raise ValueError('catalog_schema_not_current')
    except SQLAlchemyError:
        raise ValueError('catalog_schema_not_current') from None


def main(argv=None):
    from app.core.config import Settings
    from .database import make_engine
    from .sources.storage import RawStore
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw-directory', required=True, type=Path)
    parser.add_argument('--source', action='append', dest='keys', choices=[r['key'] for r in load_reviews()])
    parser.add_argument('--raw-store', type=Path, required=True)
    args = parser.parse_args(argv)
    engine = make_engine(Settings.from_env().database_url)
    try:
        try:
            require_import_schema(engine)
        except ValueError as error:
            print(json.dumps({'error':str(error)}))
            return 1
        result = import_sources(engine, args.raw_directory, RawStore(args.raw_store), keys=args.keys)
        print(json.dumps(result))
        return 0 if result['allSourcesSucceeded'] else 1
    finally:
        engine.dispose()


if __name__ == '__main__':
    raise SystemExit(main())
