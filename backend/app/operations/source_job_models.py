"""Source queue and check rows used by scheduling, controls and status."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app import admissions  # Register the referenced source tables for standalone imports.
from app.core.database import Base


class SourceJob(Base):
    __tablename__='source_jobs'
    __table_args__=(
        CheckConstraint("state IN ('queued','running','idle','failed')",name='job_state'),
        CheckConstraint('attempts >= 0 AND attempts <= max_attempts AND max_attempts BETWEEN 1 AND 20',name='job_attempts'),
        CheckConstraint('interval_seconds BETWEEN 60 AND 86400',name='job_interval'),
        CheckConstraint("(state = 'running' AND token IS NOT NULL AND lease_until IS NOT NULL) OR (state != 'running' AND token IS NULL AND lease_until IS NULL)",name='job_lease'),
        Index('ix_source_jobs_due','state','next_run_at'),
    )
    source_id: Mapped[str]=mapped_column(ForeignKey('sources.id',ondelete='CASCADE'),primary_key=True)
    state: Mapped[str]=mapped_column(String(16))
    next_run_at: Mapped[datetime]=mapped_column(DateTime(timezone=True))
    lease_until: Mapped[datetime | None]=mapped_column(DateTime(timezone=True))
    token: Mapped[str | None]=mapped_column(String(36))
    attempts: Mapped[int]=mapped_column(Integer,default=0)
    max_attempts: Mapped[int]=mapped_column(Integer,default=5)
    interval_seconds: Mapped[int]=mapped_column(Integer,default=900)
    last_error_code: Mapped[str | None]=mapped_column(String(80))


class SourceCheck(Base):
    __tablename__='source_checks'
    __table_args__=(CheckConstraint("outcome IN ('success','failed')",name='source_check_outcome'),
                   Index('ix_source_checks_time','source_id','checked_at'),Index('ix_source_checks_run','run_id'))
    id: Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid4()))
    source_id: Mapped[str]=mapped_column(ForeignKey('sources.id',ondelete='CASCADE'))
    checked_at: Mapped[datetime]=mapped_column(DateTime(timezone=True))
    outcome: Mapped[str]=mapped_column(String(16))
    error_code: Mapped[str | None]=mapped_column(String(80))
    snapshot_id: Mapped[str | None]=mapped_column(ForeignKey('source_snapshots.id',ondelete='RESTRICT'))
    run_id: Mapped[str | None]=mapped_column(String(36))
