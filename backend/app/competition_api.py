"""Read API for imported competition lists (KAN-228).

A list is shown as the official order of one published snapshot. Rows carry
only the facts the source published: rank, score, consent, priority and
participation. Candidate keys, public codes and original row references are
never returned. The only person a guest can recognise is themselves, through a
subscription confirmed earlier in the same source.
"""
from collections import Counter
from decimal import Decimal
from typing import Literal

from fastapi import Depends, HTTPException, Path, Query, Request
from pydantic import Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .admissions import Campaign, CandidateEntry, CompetitionGroup, PublishedSnapshot, Source, SourceSnapshot, Subscription, University
from .schema_base import CamelModel
from .sources.publishing import utc
from .sources.registry import PRODUCTION_REGISTRY
from .sources.status import source_status

PARTICIPATION = ('unknown', 'active', 'withdrawn', 'enrolled')


class SnapshotMeta(CamelModel):
    id: str
    fetched_at: str
    source_updated_at: str | None
    kind: Literal['live', 'archive']
    row_count: int
    complete: bool
    seats: int | None
    source_url: str | None


class SnapshotHistoryItem(CamelModel):
    id: str
    fetched_at: str
    row_count: int
    seats: int | None
    published: bool


class CompetitionRead(CamelModel):
    group_id: str
    title: str
    university_id: str
    university_name: str
    year: int
    level: str
    study_form: str
    funding: str
    category: str
    source_state: str
    snapshot: SnapshotMeta
    warnings: list[str]
    priorities_published: bool
    consent_published: bool
    my_rank: int | None
    history: list[SnapshotHistoryItem]


class CompetitionRow(CamelModel):
    official_rank: int
    score: str | None
    consent: bool | None
    priority: int | None
    participation: str
    mine: bool


class CompetitionRows(CamelModel):
    items: list[CompetitionRow]
    total: int
    next_offset: int | None


class Bin(CamelModel):
    lower: int
    upper: int
    count: int = Field(ge=0)


class Above(CamelModel):
    total: int
    consent_yes: int
    consent_no: int
    consent_unknown: int
    withdrawn: int
    priority_first: int


class CompetitionSummary(CamelModel):
    total: int
    seats: int | None
    by_consent: dict[str, int]
    by_participation: dict[str, int]
    priority_known: int
    priority_first: int
    score_known: int
    score_bins: list[Bin]
    my_rank: int | None
    above_me: Above | None
    warnings: list[str]


def published(db, group_id):
    """The group, its source and the snapshot currently published for it."""
    group = db.get(CompetitionGroup, group_id)
    if group is None:
        raise HTTPException(404, 'Конкурс не найден.')
    rows = db.execute(select(Source, SourceSnapshot).join(PublishedSnapshot, PublishedSnapshot.source_id == Source.id)
                      .join(SourceSnapshot, SourceSnapshot.id == PublishedSnapshot.snapshot_id)
                      .where(Source.group_id == group_id, Source.enabled.is_(True))
                      .order_by(SourceSnapshot.fetched_at.desc(), Source.id)).all()
    if not rows:
        raise HTTPException(404, 'Список этого конкурса ещё не импортирован.')
    source, snapshot = rows[0]
    return group, source, snapshot


def my_rank(db, owner_hash, group, snapshot):
    if owner_hash is None:
        return None
    keys = db.scalars(select(Subscription.candidate_key).where(Subscription.owner_hash == owner_hash, Subscription.group_id == group.id)).all()
    if not keys:
        return None
    return db.scalar(select(func.min(CandidateEntry.official_rank)).where(CandidateEntry.snapshot_id == snapshot.id, CandidateEntry.candidate_key.in_(keys)))


def warnings_for(group, snapshot, status, rows_known):
    codes = []
    if not snapshot.complete:
        codes.append('incomplete_list')
    if snapshot.kind == 'archive':
        codes.append('archive')
    if status and status['state'] in ('stale', 'source_error', 'quarantined'):
        codes.append('source_' + status['state'])
    if not rows_known['priority']:
        codes.append('priorities_not_published')
    if rows_known['consent_unknown']:
        codes.append('consent_unknown_rows')
    if group.funding != 'budget' or group.category != 'general':
        # Consent and seat rules differ for paid, quota and target competitions.
        codes.append('rules_not_modelled')
    if snapshot.seats is None:
        codes.append('seats_unknown')
    return codes


def known(db, snapshot):
    priority = db.scalar(select(func.count()).select_from(CandidateEntry).where(CandidateEntry.snapshot_id == snapshot.id, CandidateEntry.priority.is_not(None)))
    consent_unknown = db.scalar(select(func.count()).select_from(CandidateEntry).where(CandidateEntry.snapshot_id == snapshot.id, CandidateEntry.consent.is_(None)))
    consent = db.scalar(select(func.count()).select_from(CandidateEntry).where(CandidateEntry.snapshot_id == snapshot.id, CandidateEntry.consent.is_not(None)))
    return dict(priority=priority, consent_unknown=consent_unknown, consent=consent)


def iso(value):
    return utc(value).isoformat() if value else None


def install(app, database, owner, *, registry=PRODUCTION_REGISTRY):
    def optional_owner(request: Request, db: Session = Depends(database)):
        # Reading a public list never requires a session; a valid one only marks the guest's own row.
        if not request.cookies:
            return None
        try:
            return owner(request, db)
        except HTTPException:
            return None

    group_path = Path(min_length=1, max_length=36)

    @app.get('/api/v1/competitions/{group_id}', response_model=CompetitionRead)
    def competition(group_id: str = group_path, owner_hash: str | None = Depends(optional_owner), db: Session = Depends(database)):
        group, source, snapshot = published(db, group_id)
        campaign = db.get(Campaign, group.campaign_id)
        university = db.get(University, campaign.university_id)
        status = source_status(db, source.id, registry=registry)
        rows_known = known(db, snapshot)
        history = db.scalars(select(SourceSnapshot).where(SourceSnapshot.source_id == source.id).order_by(SourceSnapshot.fetched_at.desc()).limit(20)).all()
        return CompetitionRead(
            group_id=group.id, title=group.title, university_id=university.id, university_name=university.name, year=campaign.year,
            level=campaign.level, study_form=group.study_form, funding=group.funding, category=group.category,
            source_state=status['state'] if status else 'unknown',
            snapshot=SnapshotMeta(id=snapshot.id, fetched_at=iso(snapshot.fetched_at), source_updated_at=iso(snapshot.source_updated_at),
                                  kind=snapshot.kind, row_count=snapshot.row_count, complete=snapshot.complete, seats=snapshot.seats,
                                  source_url=status['sourceUrl'] if status else None),
            warnings=warnings_for(group, snapshot, status, rows_known), priorities_published=rows_known['priority'] > 0,
            consent_published=rows_known['consent'] > 0, my_rank=my_rank(db, owner_hash, group, snapshot),
            history=[SnapshotHistoryItem(id=s.id, fetched_at=iso(s.fetched_at), row_count=s.row_count, seats=s.seats, published=s.id == snapshot.id) for s in history])

    @app.get('/api/v1/competitions/{group_id}/rows', response_model=CompetitionRows)
    def competition_rows(group_id: str = group_path,
                         consent: Literal['yes', 'no', 'unknown'] | None = Query(None),
                         participation: Literal['unknown', 'active', 'withdrawn', 'enrolled'] | None = Query(None),
                         priority: Literal['first', 'known', 'unknown'] | None = Query(None),
                         rank_from: int = Query(1, alias='rankFrom', ge=1, le=1_000_000),
                         order: Literal['official', 'official-desc'] = 'official',
                         offset: int = Query(0, ge=0, le=100_000), limit: int = Query(50, ge=1, le=50),
                         owner_hash: str | None = Depends(optional_owner), db: Session = Depends(database)):
        group, _, snapshot = published(db, group_id)
        query = select(CandidateEntry.official_rank, CandidateEntry.score, CandidateEntry.consent, CandidateEntry.priority,
                       CandidateEntry.participation, CandidateEntry.candidate_key).where(CandidateEntry.snapshot_id == snapshot.id)
        if consent:
            query = query.where(CandidateEntry.consent.is_(None) if consent == 'unknown' else CandidateEntry.consent.is_(consent == 'yes'))
        if participation:
            query = query.where(CandidateEntry.participation == participation)
        if priority == 'first':
            query = query.where(CandidateEntry.priority == 1)
        elif priority:
            query = query.where(CandidateEntry.priority.is_(None) if priority == 'unknown' else CandidateEntry.priority.is_not(None))
        if rank_from > 1:
            query = query.where(CandidateEntry.official_rank >= rank_from) if order == 'official' else query.where(CandidateEntry.official_rank <= rank_from)
        total = db.scalar(select(func.count()).select_from(query.subquery()))
        # Only the official order: it already applies this competition's tie-breaks and extra points.
        rank = CandidateEntry.official_rank.asc() if order == 'official' else CandidateEntry.official_rank.desc()
        rows = db.execute(query.order_by(rank).offset(offset).limit(limit)).all()
        mine = set(db.scalars(select(Subscription.candidate_key).where(Subscription.owner_hash == owner_hash, Subscription.group_id == group.id)).all()) if owner_hash else set()
        items = [CompetitionRow(official_rank=r.official_rank, score=None if r.score is None else format(Decimal(r.score).normalize(), 'f'),
                                consent=r.consent, priority=r.priority, participation=r.participation, mine=r.candidate_key in mine) for r in rows]
        end = offset + len(items)
        return CompetitionRows(items=items, total=total, next_offset=end if end < total else None)

    @app.get('/api/v1/competitions/{group_id}/summary', response_model=CompetitionSummary)
    def competition_summary(group_id: str = group_path, owner_hash: str | None = Depends(optional_owner), db: Session = Depends(database)):
        group, source, snapshot = published(db, group_id)
        rows = db.execute(select(CandidateEntry.official_rank, CandidateEntry.score, CandidateEntry.consent, CandidateEntry.priority,
                                 CandidateEntry.participation).where(CandidateEntry.snapshot_id == snapshot.id)).all()
        consent_name = {True: 'yes', False: 'no', None: 'unknown'}
        by_consent = Counter(consent_name[r.consent] for r in rows)
        by_participation = Counter(r.participation for r in rows)
        scores = [Decimal(r.score) for r in rows if r.score is not None]
        bins = Counter(int(s // 10) * 10 for s in scores)
        rank = my_rank(db, owner_hash, group, snapshot)
        above = None
        if rank is not None:
            higher = [r for r in rows if r.official_rank < rank]
            above = Above(total=len(higher), consent_yes=sum(r.consent is True for r in higher), consent_no=sum(r.consent is False for r in higher),
                          consent_unknown=sum(r.consent is None for r in higher), withdrawn=sum(r.participation == 'withdrawn' for r in higher),
                          priority_first=sum(r.priority == 1 for r in higher))
        status = source_status(db, source.id, registry=registry)
        rows_known = dict(priority=sum(r.priority is not None for r in rows), consent_unknown=by_consent['unknown'])
        return CompetitionSummary(
            total=len(rows), seats=snapshot.seats, by_consent={k: by_consent[k] for k in ('yes', 'no', 'unknown')},
            by_participation={k: by_participation[k] for k in PARTICIPATION}, priority_known=rows_known['priority'],
            priority_first=sum(r.priority == 1 for r in rows), score_known=len(scores),
            # Empty ranges between the lowest and highest score stay visible as zeros.
            score_bins=[Bin(lower=k, upper=k + 10, count=bins[k]) for k in range(min(bins), max(bins) + 10, 10)] if bins else [],
            my_rank=rank, above_me=above, warnings=warnings_for(group, snapshot, status, rows_known))
