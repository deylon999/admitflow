#!/usr/bin/env python3
"""Advance ONLY a disposable fixture database; no external network or web endpoint."""
import json,os,sys
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/tests')]
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import make_engine
from app.admissions import PublishedSnapshot,SourceSnapshot
from app.sources.registry import runtime_registry
from app.sources.publishing import publish
from app.sources.storage import RawStore
from test_sgu_adapter import KEY,BINDING
from test_scenario_storage import changed_consent
from types import SimpleNamespace
path=Path(os.environ['E2E_SOURCE_CONTROL'])
if path.parent!=Path('/tmp') or path.stat().st_mode&0o077:raise SystemExit('Unsafe fixture control')
control=json.loads(path.read_text());url=urlparse(control['url'])
if control.get('fixtureOnly') is not True or url.hostname!='127.0.0.1' or url.path!='/admitflow_test_native':raise SystemExit('Not disposable fixture database')
os.environ['SOURCE_IDENTITY_KEY']=KEY.hex()
engine=make_engine(control['url'])
try:
 registry=runtime_registry();parsed,raw=changed_consent(SimpleNamespace(state=SimpleNamespace(source_registry=registry)),None)
 with Session(engine) as db:
  pointer=db.get(PublishedSnapshot,BINDING.source_id);old=db.get(SourceSnapshot,pointer.snapshot_id)
  if old.payload_hash==raw.payload_hash:raise SystemExit('Fixture change already applied')
 publish(engine,BINDING.source_id,parsed,raw,RawStore(Path(control['raw'])),registry=registry)
 print('Synthetic fixture change published; no external HTTP')
finally:engine.dispose()
