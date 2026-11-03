from dataclasses import replace
from datetime import timedelta

from sqlalchemy.orm import Session

from app.admissions import PublishedSnapshot,Source
from app.jobs import SourceJob,enqueue
from app.sources.registry import Registry
from app.sources.storage import RawStore
from app.worker import run_once
from sgu_helpers import seed_sgu
from test_sgu_adapter import BINDING,KEY,make_adapter,response


def test_real_format_worker_success_then_bad_page_retains_last_good(source_engine,tmp_path):
    seed_sgu(source_engine);enqueue(source_engine,BINDING.source_id,now=response().fetched_at)
    registry=Registry((make_adapter(KEY),));store=RawStore(tmp_path/'raw');raw=response()
    assert run_once(source_engine,store,registry=registry,now=lambda:raw.fetched_at,fetch=lambda *_,**__:raw)['state']=='success'
    with Session(source_engine) as db:first=db.get(PublishedSnapshot,BINDING.source_id).snapshot_id
    later=raw.fetched_at+timedelta(seconds=901)
    bad=response(b'<html>Login required</html>');bad=replace(bad,fetched_at=later)
    assert run_once(source_engine,store,registry=registry,now=lambda:later,fetch=lambda *_,**__:bad)['state']=='failed'
    with Session(source_engine) as db:
        assert db.get(PublishedSnapshot,BINDING.source_id).snapshot_id==first
        assert db.get(SourceJob,BINDING.source_id).state=='failed'
        assert db.get(Source,BINDING.source_id).last_error_code=='invalid_format'
