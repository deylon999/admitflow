"""Database queue: one row per source, expiring leases and fencing tokens."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, and_, or_, select, text
from sqlalchemy.orm import Mapped, Session, mapped_column

from .admissions import Source
from .database import Base
from .sources.publishing import FETCH_CODES, QUARANTINE_CODES, STORAGE_RETRY_CODES, lock_source, utc


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


@dataclass(frozen=True,repr=False)
class Lease:
    source_id: str
    token: str
    attempt: int


class LostLease(Exception):
    pass


def clock():
    return datetime.now(timezone.utc)


def enqueue(engine,source_id,*,now=None,interval_seconds=900,max_attempts=5):
    now=now or clock()
    if type(interval_seconds) is not int or type(max_attempts) is not int or not 60 <= interval_seconds <= 86400 or not 1 <= max_attempts <= 20:
        raise ValueError('invalid_queue_policy')
    with Session(engine) as db:
        source=lock_source(db,engine,source_id)
        if not source.enabled:
            return False
        job=db.scalar(select(SourceJob).where(SourceJob.source_id==source_id).with_for_update())
        if job:
            if job.state in ('queued','running') or utc(job.next_run_at)>now:
                return False
            job.state='queued'
            job.attempts=0
            job.last_error_code=None
            job.interval_seconds=interval_seconds
            job.max_attempts=max_attempts
            job.next_run_at=now
        else:
            db.add(SourceJob(source_id=source_id,state='queued',next_run_at=now,attempts=0,max_attempts=max_attempts,interval_seconds=interval_seconds))
        db.commit()
        return True


def claim(engine,*,now=None,lease_seconds=120):
    now=now or clock()
    if not 30 <= lease_seconds <= 900:
        raise ValueError('invalid_lease_duration')
    with Session(engine) as db:
        if engine.dialect.name=='sqlite':
            db.execute(text('BEGIN IMMEDIATE'))
        query=(select(SourceJob).join(Source).where(Source.enabled.is_(True),or_(and_(SourceJob.state.in_(('queued','idle')),SourceJob.next_run_at<=now),and_(SourceJob.state=='running',SourceJob.lease_until<=now))).order_by(SourceJob.next_run_at,SourceJob.source_id).with_for_update(skip_locked=True,of=SourceJob))
        # Expired final attempts are retired instead of reclaimed forever.
        for job in db.scalars(query.limit(100)).all():
            if job.attempts>=job.max_attempts:
                job.state='failed'
                job.token=job.lease_until=None
                job.last_error_code='lease_exhausted'
                job.next_run_at=now+timedelta(seconds=job.interval_seconds)
                continue
            job.attempts+=1
            job.state='running'
            job.token=str(uuid4())
            job.lease_until=now+timedelta(seconds=lease_seconds)
            result=Lease(job.source_id,job.token,job.attempts)
            db.commit()
            return result
        db.commit()
        return None


def guard_lease(db,lease,*,now=None):
    now=now or clock()
    job=db.scalar(select(SourceJob).where(SourceJob.source_id==lease.source_id).with_for_update())
    if not job or job.state!='running' or job.token!=lease.token or utc(job.lease_until)<=now:
        raise LostLease('lease_lost')
    return job


def complete(engine,lease,*,now=None):
    now=now or clock()
    with Session(engine) as db:
        lock_source(db,engine,lease.source_id)
        job=guard_lease(db,lease,now=now)
        job.state='idle'
        job.token=job.lease_until=None
        job.attempts=0
        job.last_error_code=None
        job.next_run_at=now+timedelta(seconds=job.interval_seconds)
        db.commit()


def fail(engine,lease,code,*,retry_after=None,now=None):
    now=now or clock()
    safe_code=code if code in FETCH_CODES|QUARANTINE_CODES|STORAGE_RETRY_CODES else 'internal_error'
    with Session(engine) as db:
        source=lock_source(db,engine,lease.source_id)
        job=guard_lease(db,lease,now=now)
        retry=retry_after is not None and job.attempts<job.max_attempts
        delay=max(job.interval_seconds,min(86400,max(30,retry_after or 0)),min(3600,30*2**(job.attempts-1)))
        job.state='queued' if retry else 'failed'
        job.token=job.lease_until=None
        job.next_run_at=now+timedelta(seconds=delay)
        job.last_error_code=safe_code
        if source.last_checked_at is None or utc(source.last_checked_at)<=now:
            source.last_checked_at=now
            source.last_error_code=safe_code
        db.commit()


def disable(engine,source_id,*,now=None):
    now=now or clock()
    with Session(engine) as db:
        source=lock_source(db,engine,source_id)
        source.enabled=False
        job=db.scalar(select(SourceJob).where(SourceJob.source_id==source_id).with_for_update())
        if job:
            job.state='failed'
            job.token=job.lease_until=None
            job.last_error_code='source_disabled'
            job.next_run_at=now+timedelta(seconds=job.interval_seconds)
        db.commit()
