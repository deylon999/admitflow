"""Bounded operational audit and explicit fenced source controls."""
from dataclasses import replace
from datetime import datetime,timezone,timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session
from .admissions import SourceOperation
from .sources.contracts import AdapterError
from .sources.publishing import lock_source,binding_from_db,utc

ACTIONS=frozenset({'register','enable','disable','enqueue','quarantine','resume','enable-scenarios'})
OUTCOMES=frozenset({'created','updated','unchanged','queued','deferred','disabled','held','enabled','resumed'})

def record(db,source,action,outcome,*,now=None):
    if action not in ACTIONS or outcome not in OUTCOMES:raise ValueError('invalid_operation_audit')
    db.add(SourceOperation(source_id=source.id,action=action,outcome=outcome,adapter_version=source.adapter_version,created_at=now or datetime.now(timezone.utc)))


def control(engine,source_id,action,*,registry,now=None):
    from .jobs import SourceJob
    if action not in ('enable','quarantine','resume'):raise ValueError('invalid_source_control')
    now=now or datetime.now(timezone.utc)
    with Session(engine) as db:
        source=lock_source(db,engine,source_id)
        job=db.scalar(select(SourceJob).where(SourceJob.source_id==source_id).with_for_update())
        if action=='quarantine':
            source.last_error_code='operator_quarantine'
            if job:
                job.state='failed';job.token=job.lease_until=None;job.last_error_code='operator_quarantine'
                job.next_run_at=max(utc(job.next_run_at),now+timedelta(seconds=job.interval_seconds))
            outcome='held'
        else:
            registry.resolve(replace(binding_from_db(db,source),enabled=True))
            if action=='enable' and source.last_error_code=='operator_quarantine':raise AdapterError('operator_quarantine')
            source.enabled=True
            if action=='resume':
                source.last_error_code='refresh_pending'
                if job:
                    job.state='queued';job.token=job.lease_until=None;job.attempts=0;job.last_error_code=None
                    # Keep next_run_at: resuming cannot bypass source rate limits.
            outcome='enabled' if action=='enable' else 'resumed'
        record(db,source,action,outcome,now=now);db.commit()
        return {'sourceId':source_id,'enabled':source.enabled,'action':action,'outcome':outcome}
