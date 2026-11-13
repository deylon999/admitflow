"""Account persistence only. Never reuse guest owner hashes as account identities."""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class AccountUser(Base):
    __tablename__ = 'account_users'
    __table_args__ = (
        CheckConstraint("status IN ('active', 'disabled')", name='account_user_status'),
        CheckConstraint('email = lower(trim(email)) AND length(email) BETWEEN 3 AND 254', name='account_email_normalized'),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(String(16), default='active')
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    password_changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class AccountSession(Base):
    __tablename__ = 'account_sessions'
    __table_args__ = (
        CheckConstraint('created_at < access_expires_at AND access_expires_at <= expires_at', name='account_access_lifetime'),
        CheckConstraint('created_at < idle_expires_at AND idle_expires_at <= expires_at', name='account_idle_lifetime'),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey('account_users.id', ondelete='CASCADE'), index=True)
    access_hash: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    access_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    idle_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AccountRefreshToken(Base):
    __tablename__ = 'account_refresh_tokens'
    __table_args__ = (CheckConstraint('created_at < expires_at', name='account_refresh_lifetime'),)
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey('account_sessions.id', ondelete='CASCADE'), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AccountActionToken(Base):
    __tablename__ = 'account_action_tokens'
    __table_args__ = (
        CheckConstraint("purpose IN ('verify_email', 'reset_password')", name='account_action_purpose'),
        CheckConstraint('created_at < expires_at', name='account_action_lifetime'),
    )
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('account_users.id', ondelete='CASCADE'), index=True)
    purpose: Mapped[str] = mapped_column(String(24))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AccountCsrfContext(Base):
    __tablename__ = 'account_csrf_contexts'
    __table_args__ = (CheckConstraint('created_at < expires_at', name='account_csrf_lifetime'),)
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    # A synchronizer token is not an account credential; the context cookie is HttpOnly.
    csrf_token: Mapped[str] = mapped_column(String(64))
    session_id: Mapped[str | None] = mapped_column(ForeignKey('account_sessions.id', ondelete='CASCADE'), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class AccountRateBucket(Base):
    __tablename__ = 'account_rate_buckets'
    __table_args__ = (
        CheckConstraint('used >= 0', name='account_rate_nonnegative'),
        CheckConstraint('window_start < expires_at', name='account_rate_lifetime'),
    )
    operation: Mapped[str] = mapped_column(String(40), primary_key=True)
    subject_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    used: Mapped[int] = mapped_column(Integer)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
