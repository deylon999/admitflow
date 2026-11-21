from datetime import datetime
from uuid import uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, make_engine


class BrowserSession(Base):
    __tablename__ = 'browser_sessions'
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class Watch(Base):
    __tablename__ = 'watches'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    owner_hash: Mapped[str] = mapped_column(ForeignKey('browser_sessions.token_hash', ondelete='CASCADE'), index=True)
    university: Mapped[str] = mapped_column(String(160))
    title: Mapped[str] = mapped_column(String(200))
    source_url: Mapped[str] = mapped_column(String(2048))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class LookupBudget(Base):
    __tablename__ = 'lookup_budgets'
    owner_hash: Mapped[str] = mapped_column(ForeignKey('browser_sessions.token_hash', ondelete='CASCADE'), primary_key=True)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used: Mapped[int] = mapped_column(Integer)


class Snapshot(Base):
    __tablename__ = 'snapshots'
    __table_args__ = (
        CheckConstraint('rank >= 1 AND rank <= 1000000', name='rank_range'),
        CheckConstraint('seats >= 1 AND seats <= 1000000', name='seats_range'),
        CheckConstraint('excluded >= 0 AND no_consent >= 0 AND excluded + no_consent < rank', name='groups_above'),
        Index('ix_snapshots_watch_time', 'watch_id', 'captured_at'),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    watch_id: Mapped[str] = mapped_column(ForeignKey('watches.id', ondelete='CASCADE'))
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    rank: Mapped[int] = mapped_column(Integer)
    seats: Mapped[int] = mapped_column(Integer)
    excluded: Mapped[int] = mapped_column(Integer)
    no_consent: Mapped[int] = mapped_column(Integer)
    source_kind: Mapped[str] = mapped_column(String(24), default='manual')
    model_version: Mapped[str] = mapped_column(String(32), default='manual-v1')


class OperationRecord(Base):
    __tablename__ = 'operation_records'
    __table_args__ = (
        CheckConstraint("(response_status = 201 AND response IS NOT NULL) OR (response_status = 410 AND response IS NULL)", name='operation_response_state'),
    )
    owner_hash: Mapped[str] = mapped_column(ForeignKey('browser_sessions.token_hash', ondelete='CASCADE'), primary_key=True)
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    fingerprint: Mapped[str] = mapped_column(String(64))
    watch_id: Mapped[str | None] = mapped_column(ForeignKey('watches.id', ondelete='SET NULL'), index=True)
    response: Mapped[dict | None] = mapped_column(JSON(none_as_null=True))
    response_status: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
