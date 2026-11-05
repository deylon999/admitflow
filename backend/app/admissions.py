"""Shared admissions data, independent of a browser's manual calculations."""
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, Integer, JSON, Numeric, String, UniqueConstraint, event
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base
from .catalog_search import university_search,group_search


def new_id():
    return str(uuid4())


class University(Base):
    __tablename__ = 'universities'
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    name: Mapped[str] = mapped_column(String(300))
    search_name: Mapped[str] = mapped_column(String(1000),default=university_search,server_default='')
    region: Mapped[str | None] = mapped_column(String(120))
    parent_id: Mapped[str | None] = mapped_column(ForeignKey('universities.id', ondelete='RESTRICT'))
    official_url: Mapped[str] = mapped_column(String(2048))
    provenance_url: Mapped[str] = mapped_column(String(2048))
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Campaign(Base):
    __tablename__ = 'campaigns'
    __table_args__ = (
        UniqueConstraint('university_id', 'year', 'level', name='uq_campaign_identity'),
        CheckConstraint('year >= 2000 AND year <= 2100', name='campaign_year'),
        CheckConstraint("level IN ('bachelor', 'specialist', 'master')", name='campaign_level'),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    university_id: Mapped[str] = mapped_column(ForeignKey('universities.id', ondelete='RESTRICT'))
    year: Mapped[int] = mapped_column(Integer)
    level: Mapped[str] = mapped_column(String(24))


class CompetitionGroup(Base):
    __tablename__ = 'competition_groups'
    __table_args__ = (
        UniqueConstraint('campaign_id', 'official_id', name='uq_group_identity'),
        CheckConstraint('seats IS NULL OR seats >= 0', name='group_seats'),
        CheckConstraint("coverage IN ('candidate', 'manual', 'automatic', 'suspended')", name='group_coverage'),
        CheckConstraint("coverage != 'automatic' OR rules_version IS NOT NULL", name='automatic_requires_rules'),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    campaign_id: Mapped[str] = mapped_column(ForeignKey('campaigns.id', ondelete='RESTRICT'))
    official_id: Mapped[str] = mapped_column(String(160))
    title: Mapped[str] = mapped_column(String(300))
    search_text: Mapped[str] = mapped_column(String(1500),default=group_search,server_default='')
    study_form: Mapped[str] = mapped_column(String(40))
    funding: Mapped[str] = mapped_column(String(40))
    category: Mapped[str] = mapped_column(String(80))
    seats: Mapped[int | None] = mapped_column(Integer)
    coverage: Mapped[str] = mapped_column(String(24), default='candidate')
    rules_version: Mapped[str | None] = mapped_column(String(80))


class Source(Base):
    __tablename__ = 'sources'
    __table_args__ = (
        UniqueConstraint('id', 'group_id', name='uq_source_group'),
        CheckConstraint('NOT enabled OR adapter_version IS NOT NULL', name='enabled_source_has_adapter'),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    group_id: Mapped[str] = mapped_column(ForeignKey('competition_groups.id', ondelete='RESTRICT'), index=True)
    url: Mapped[str] = mapped_column(String(2048))
    domain: Mapped[str] = mapped_column(String(255))
    adapter_version: Mapped[str | None] = mapped_column(String(80))
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    snapshot_kind: Mapped[str] = mapped_column(String(16), default='archive', server_default='archive')
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error_code: Mapped[str | None] = mapped_column(String(80))


class SourceSnapshot(Base):
    __tablename__ = 'source_snapshots'
    __table_args__ = (
        UniqueConstraint('source_id', 'payload_hash', 'adapter_version', name='uq_source_payload_version'),
        UniqueConstraint('source_id', 'id', name='uq_source_snapshot_id'),
        UniqueConstraint('id', 'group_id', name='uq_snapshot_group'),
        ForeignKeyConstraint(['source_id', 'group_id'], ['sources.id', 'sources.group_id'], name='fk_snapshot_source_group'),
        CheckConstraint("kind IN ('live', 'archive')", name='snapshot_kind'),
        CheckConstraint('row_count >= 0', name='snapshot_rows'),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    source_id: Mapped[str] = mapped_column(ForeignKey('sources.id', ondelete='RESTRICT'))
    group_id: Mapped[str] = mapped_column(ForeignKey('competition_groups.id', ondelete='RESTRICT'))
    payload_hash: Mapped[str] = mapped_column(String(64))
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    kind: Mapped[str] = mapped_column(String(16))
    row_count: Mapped[int] = mapped_column(Integer)
    complete: Mapped[bool] = mapped_column(Boolean, default=False)
    adapter_version: Mapped[str | None] = mapped_column(String(80))
    normalized_hash: Mapped[str | None] = mapped_column(String(64))
    seats: Mapped[int | None] = mapped_column(Integer)
    warnings: Mapped[list | None] = mapped_column(JSON)
    fetched_url: Mapped[str | None] = mapped_column(String(2048))
    content_type: Mapped[str | None] = mapped_column(String(100))
    charset: Mapped[str | None] = mapped_column(String(80))


class CandidateEntry(Base):
    __tablename__ = 'candidate_entries'
    __table_args__ = (
        UniqueConstraint('snapshot_id', 'official_rank', name='uq_snapshot_rank'),
        CheckConstraint('official_rank > 0', name='entry_rank'),
        CheckConstraint('priority IS NULL OR priority > 0', name='entry_priority'),
        CheckConstraint("participation IN ('unknown', 'active', 'withdrawn', 'enrolled')", name='entry_participation'),
    )
    snapshot_id: Mapped[str] = mapped_column(ForeignKey('source_snapshots.id', ondelete='CASCADE'), primary_key=True)
    candidate_key: Mapped[str] = mapped_column(String(100), primary_key=True)
    official_rank: Mapped[int] = mapped_column(Integer)
    score: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    consent: Mapped[bool | None] = mapped_column(Boolean)
    priority: Mapped[int | None] = mapped_column(Integer)
    participation: Mapped[str] = mapped_column(String(24), default='unknown')
    row_ref: Mapped[str | None] = mapped_column(String(100))


class PublishedSnapshot(Base):
    __tablename__ = 'published_snapshots'
    __table_args__ = (
        ForeignKeyConstraint(['source_id', 'snapshot_id'], ['source_snapshots.source_id', 'source_snapshots.id'], name='fk_published_source_snapshot'),
    )
    source_id: Mapped[str] = mapped_column(ForeignKey('sources.id', ondelete='RESTRICT'), primary_key=True)
    snapshot_id: Mapped[str] = mapped_column(ForeignKey('source_snapshots.id', ondelete='RESTRICT'))


class Subscription(Base):
    __tablename__ = 'subscriptions'
    __table_args__ = (
        UniqueConstraint('owner_hash', 'group_id', 'candidate_key', name='uq_subscription'),
        UniqueConstraint('id', 'group_id', name='uq_subscription_group'),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_hash: Mapped[str] = mapped_column(ForeignKey('browser_sessions.token_hash', ondelete='CASCADE'), index=True)
    group_id: Mapped[str] = mapped_column(ForeignKey('competition_groups.id', ondelete='RESTRICT'))
    candidate_key: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Assessment(Base):
    __tablename__ = 'assessments'
    __table_args__ = (
        UniqueConstraint('subscription_id', 'snapshot_id', 'rules_version', name='uq_assessment'),
        ForeignKeyConstraint(['subscription_id', 'group_id'], ['subscriptions.id', 'subscriptions.group_id'], name='fk_assessment_subscription_group', ondelete='CASCADE'),
        ForeignKeyConstraint(['snapshot_id', 'group_id'], ['source_snapshots.id', 'source_snapshots.group_id'], name='fk_assessment_snapshot_group'),
        CheckConstraint("state IN ('within', 'conditional', 'out', 'unsupported', 'insufficient_data')", name='assessment_state'),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    subscription_id: Mapped[str] = mapped_column(ForeignKey('subscriptions.id', ondelete='CASCADE'))
    group_id: Mapped[str] = mapped_column(ForeignKey('competition_groups.id', ondelete='RESTRICT'))
    snapshot_id: Mapped[str] = mapped_column(ForeignKey('source_snapshots.id', ondelete='RESTRICT'))
    rules_version: Mapped[str] = mapped_column(String(80))
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    state: Mapped[str] = mapped_column(String(32))
    facts: Mapped[dict] = mapped_column(JSON)
    assumptions: Mapped[list] = mapped_column(JSON)


class ChangeEvent(Base):
    __tablename__='change_events'
    id: Mapped[str]=mapped_column(String(36),primary_key=True,default=new_id)
    assessment_id: Mapped[str]=mapped_column(ForeignKey('assessments.id',ondelete='CASCADE'),unique=True,index=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True))
    seen_at: Mapped[datetime | None]=mapped_column(DateTime(timezone=True))


class SourceOperation(Base):
    __tablename__='source_operations'
    id: Mapped[str]=mapped_column(String(36),primary_key=True,default=new_id)
    source_id: Mapped[str]=mapped_column(ForeignKey('sources.id',ondelete='CASCADE'),index=True)
    action: Mapped[str]=mapped_column(String(24))
    outcome: Mapped[str]=mapped_column(String(24))
    adapter_version: Mapped[str | None]=mapped_column(String(80))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True))


@event.listens_for(University,'before_insert')
@event.listens_for(University,'before_update')
def normalize_university_search(_mapper,_connection,row):
    row.search_name=row.name.casefold()


@event.listens_for(CompetitionGroup,'before_insert')
@event.listens_for(CompetitionGroup,'before_update')
def normalize_group_search(_mapper,_connection,row):
    row.search_text=f'{row.title} {row.official_id}'.casefold()
