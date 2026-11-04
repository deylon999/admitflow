"""Operational signals: structured events, worker liveness, source->run->snapshot->assessment.

Nothing here reads candidate rows, raw payloads, URLs with credentials or exception text.
"""
import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
import json
import logging
import sys

from sqlalchemy import DateTime, String, delete, func, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from .admissions import Assessment, Source, SourceSnapshot
from .database import Base
from .jobs import SourceCheck, SourceJob
from .sources.publishing import utc
from .sources.status import source_status

WORKER_STALE_SECONDS = 180
HEARTBEAT_RETENTION = timedelta(days=7)
UNHEALTHY_SOURCE_STATES = frozenset({'source_error','quarantined','stale'})


class WorkerHeartbeat(Base):
    __tablename__='worker_heartbeats'
    worker_id: Mapped[str]=mapped_column(String(36),primary_key=True)
    started_at: Mapped[datetime]=mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime]=mapped_column(DateTime(timezone=True))
    last_state: Mapped[str]=mapped_column(String(16))


def worker_logger():
    logger=logging.getLogger('admitflow.worker')
    logger.setLevel(logging.INFO)
    if not logger.handlers and not logging.getLogger().handlers:
        logger.addHandler(logging.StreamHandler(sys.stdout))
    return logger


def log_event(event,**fields):
    worker_logger().info(json.dumps(dict(event=event,**fields),separators=(',',':'),ensure_ascii=False))


def beat(engine,worker_id,started_at,state,*,now=None):
    now=now or datetime.now(timezone.utc)
    with Session(engine) as db:
        value=db.get(WorkerHeartbeat,worker_id)
        if value is None:
            db.add(WorkerHeartbeat(worker_id=worker_id,started_at=started_at,last_seen_at=now,last_state=state[:16]))
            db.execute(delete(WorkerHeartbeat).where(WorkerHeartbeat.last_seen_at<now-HEARTBEAT_RETENTION))
        else:
            value.last_seen_at=now
            value.last_state=state[:16]
        db.commit()


def worker_status(db,*,now,stale_seconds=WORKER_STALE_SECONDS):
    last=db.scalar(select(func.max(WorkerHeartbeat.last_seen_at)))
    if last is None:
        return dict(state='never_seen',lastSeenAt=None,ageSeconds=None)
    age=max(0,round((now-utc(last)).total_seconds()))
    return dict(state='alive' if age<=stale_seconds else 'stale',lastSeenAt=utc(last).isoformat(),ageSeconds=age)


def system_status(db,*,now=None,registry=None):
    """Separate from HTTP health: a dead worker or stale source must not look like a dead API."""
    now=now or datetime.now(timezone.utc)
    options={'registry':registry} if registry is not None else {}
    states=Counter()
    for source_id in db.scalars(select(Source.id)).all():
        status=source_status(db,source_id,now=now,**options)
        if status:
            states[status['state']]+=1
    jobs=Counter(db.scalars(select(SourceJob.state)).all())
    overdue=db.scalar(select(func.count()).select_from(SourceJob).where(SourceJob.state.in_(('queued','idle')),SourceJob.next_run_at<now-timedelta(minutes=10)))
    worker=worker_status(db,now=now)
    needs_worker=sum(jobs.values())>0
    degraded=(needs_worker and worker['state']!='alive') or any(states[name] for name in UNHEALTHY_SOURCE_STATES) or bool(overdue)
    return dict(status='degraded' if degraded else 'ok',checkedAt=now.isoformat(),worker=worker,
                sources=dict(total=sum(states.values()),byState=dict(sorted(states.items()))),
                jobs=dict(byState=dict(sorted(jobs.items())),overdue=overdue))


def trace_run(db,run_id):
    """Rebuild one attempt from its log runId. Counts only: no candidate data."""
    check=db.scalar(select(SourceCheck).where(SourceCheck.run_id==run_id))
    if check is None:
        return None
    snapshot=db.get(SourceSnapshot,check.snapshot_id) if check.snapshot_id else None
    assessments=db.scalar(select(func.count()).select_from(Assessment).where(Assessment.snapshot_id==check.snapshot_id)) if check.snapshot_id else 0
    return dict(runId=run_id,sourceId=check.source_id,checkedAt=utc(check.checked_at).isoformat(),outcome=check.outcome,errorCode=check.error_code,
                snapshot=dict(id=snapshot.id,fetchedAt=utc(snapshot.fetched_at).isoformat(),kind=snapshot.kind,rowCount=snapshot.row_count,adapterVersion=snapshot.adapter_version) if snapshot else None,
                assessments=assessments)


def main(argv=None):
    from .config import Settings
    from .database import make_engine
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='command',required=True)
    commands.add_parser('status')
    trace=commands.add_parser('trace')
    trace.add_argument('run_id')
    args=parser.parse_args(argv)
    engine=make_engine(Settings.from_env().database_url)
    try:
        with Session(engine) as db:
            result=system_status(db) if args.command=='status' else trace_run(db,args.run_id)
    finally:
        engine.dispose()
    print(json.dumps(result,ensure_ascii=False))
    return 0 if result else 1


if __name__=='__main__':
    raise SystemExit(main())
