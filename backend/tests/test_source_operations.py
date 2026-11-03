from dataclasses import replace
from datetime import timedelta
import pytest
from sqlalchemy import func,select
from sqlalchemy.orm import Session
from app.admissions import Source,SourceOperation,PublishedSnapshot
from app.jobs import enqueue,claim,renew,disable,LostLease,SourceJob
from app.source_operations import control
from app.sources.cli import operate
from app.sources.contracts import AdapterError
from app.sources.publishing import publish,record_failure,utc
from app.sources.storage import RawStore
from app.sources.pilots import register_sgu
from test_sgu_adapter import BINDING,KEY,make_adapter,response
from app.sources.registry import Registry


def test_operator_quarantine_fences_running_worker_and_resume_preserves_rate_limit(source_engine,tmp_path):
 registry=Registry((make_adapter(KEY),));register_sgu(source_engine,enable=True,registry=registry);raw=response();now=raw.fetched_at
 published=publish(source_engine,BINDING.source_id,registry.resolve(BINDING).parse(raw,BINDING),raw,RawStore(tmp_path/'raw'),registry=registry)
 assert enqueue(source_engine,BINDING.source_id,now=now);lease=claim(source_engine,now=now);assert lease
 control(source_engine,BINDING.source_id,'quarantine',registry=registry,now=now)
 assert claim(source_engine,now=now+timedelta(days=1)) is None
 assert not enqueue(source_engine,BINDING.source_id,now=now+timedelta(days=1))
 with pytest.raises(LostLease):renew(source_engine,lease,now=now)
 with pytest.raises(AdapterError,match='operator_quarantine'):publish(source_engine,BINDING.source_id,registry.resolve(BINDING).parse(raw,BINDING),raw,RawStore(tmp_path/'raw'),registry=registry)
 record_failure(source_engine,BINDING.source_id,'network_error',now+timedelta(seconds=1))
 assert operate(source_engine,'status',BINDING.source_id,registry=registry)['state']=='quarantined'
 for register in (lambda:register_sgu(source_engine,enable=True,registry=registry),lambda:control(source_engine,BINDING.source_id,'enable',registry=registry)):
  with pytest.raises(AdapterError,match='operator_quarantine'):register()
 control(source_engine,BINDING.source_id,'resume',registry=registry,now=now+timedelta(seconds=1))
 assert claim(source_engine,now=now+timedelta(seconds=899)) is None
 with Session(source_engine) as db:
  source=db.get(Source,BINDING.source_id);assert db.get(PublishedSnapshot,source.id).snapshot_id==published
  assert source.last_error_code=='refresh_pending' and utc(source.last_success_at)==now
  assert {op.action for op in db.scalars(select(SourceOperation))}=={'enable','enqueue','quarantine','resume'}
 assert claim(source_engine,now=now+timedelta(seconds=901)) is not None
 disable(source_engine,BINDING.source_id,now=now+timedelta(seconds=902));status=operate(source_engine,'status',BINDING.source_id,registry=registry)
 assert status['state']=='disabled' and status['configuredAdapterVersion']==BINDING.adapter_version and any(op['action']=='disable' for op in status['operations'])
 assert 'token' not in status['job']


def test_operator_enable_requires_attested_unchanged_binding_and_failed_control_is_atomic(source_engine):
 registry=Registry((make_adapter(KEY),));register_sgu(source_engine,registry=registry)
 assert operate(source_engine,'enable',BINDING.source_id,registry=registry)['enabled']
 disable(source_engine,BINDING.source_id)
 with Session(source_engine) as db:
  source=db.get(Source,BINDING.source_id);source.adapter_version='unreviewed-v99';db.commit()
  before=db.scalar(select(func.count()).select_from(SourceOperation))
 with pytest.raises(AdapterError):operate(source_engine,'enable',BINDING.source_id,registry=registry)
 with Session(source_engine) as db:
  assert not db.get(Source,BINDING.source_id).enabled
  assert db.scalar(select(func.count()).select_from(SourceOperation))==before
 with pytest.raises(AdapterError):operate(source_engine,'quarantine','unknown',registry=registry)
