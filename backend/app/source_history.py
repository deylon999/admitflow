"""Immutable, versioned source facts. This never predicts admission."""
from datetime import datetime,timezone
from fastapi import HTTPException
from sqlalchemy import and_, func, or_, select
from .admissions import Assessment, CandidateEntry, SourceSnapshot, Subscription

FACT_VERSION = 'source-facts-v1'
VERSIONS = ('source-confirmation-v1', FACT_VERSION)


def assessment_clock():
    return datetime.now(timezone.utc)


def append_snapshot_facts(db, snapshot):
    # Only subscriptions confirmed in this exact source, never group-wide ID matching.
    confirmed = select(Assessment.subscription_id).join(SourceSnapshot, Assessment.snapshot_id == SourceSnapshot.id).where(
        Assessment.rules_version == 'source-confirmation-v1', SourceSnapshot.source_id == snapshot.source_id)
    subscriptions = db.scalars(select(Subscription).where(Subscription.id.in_(confirmed)).with_for_update()).all()
    from .source_api import candidate_fact
    for subscription in subscriptions:
        if db.scalar(select(Assessment.id).where(Assessment.subscription_id == subscription.id, Assessment.snapshot_id == snapshot.id,
                                                Assessment.rules_version.in_(VERSIONS))):
            continue
        row = db.get(CandidateEntry, (snapshot.id, subscription.candidate_key))
        facts = {'present': row is not None, 'sourceId': snapshot.source_id, 'dataKind': snapshot.kind,
                 'candidate': candidate_fact(row).model_dump(mode='json', by_alias=True) if row else None}
        db.add(Assessment(subscription_id=subscription.id, group_id=subscription.group_id, snapshot_id=snapshot.id,
                          rules_version=FACT_VERSION, assessed_at=assessment_clock(), state='unsupported', facts=facts,
                          assumptions=['Факты архивного снимка; отсутствие строки не подтверждает отзыв или отказ.']))


def history_rows(db, subscription_id, owner_hash, before=None, limit=20):
    value = db.scalar(select(Subscription).where(Subscription.id == subscription_id, Subscription.owner_hash == owner_hash))
    if value is None:
        raise HTTPException(404, 'Архивная запись не найдена.')
    query = select(Assessment, SourceSnapshot).join(SourceSnapshot, Assessment.snapshot_id == SourceSnapshot.id).where(
        Assessment.subscription_id == value.id, Assessment.rules_version.in_(VERSIONS))
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    if before:
        cursor = db.execute(query.where(Assessment.id == before)).first()
        if cursor is None:
            raise HTTPException(400, 'Курсор истории недействителен.')
        _, snapshot = cursor
        query = query.where(or_(SourceSnapshot.fetched_at < snapshot.fetched_at,
                                and_(SourceSnapshot.fetched_at == snapshot.fetched_at, Assessment.id < before)))
    rows = db.execute(query.order_by(SourceSnapshot.fetched_at.desc(), Assessment.id.desc()).limit(limit+1)).all()
    return value, rows[:limit], rows[limit-1][0].id if len(rows)>limit else None, total
