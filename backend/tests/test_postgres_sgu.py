from concurrent.futures import ThreadPoolExecutor
from threading import Event

from fastapi.testclient import TestClient
import pytest

from app.config import Settings
from app.jobs import enqueue
from app.main import create_app
from app.sources.registry import Registry
from app.sources.storage import RawStore
from app.worker import run_once
from native_support import postgres_engine
from sgu_helpers import seed_sgu
from test_api import HEADERS
from test_sgu_adapter import BINDING,KEY,make_adapter,response
from test_sgu_worker import test_real_format_worker_success_then_bad_page_retains_last_good

pytestmark=pytest.mark.postgres


@pytest.fixture
def source_engine(postgres_engine):return postgres_engine


def test_blocked_real_source_worker_does_not_block_manual_api(source_engine,tmp_path):
    seed_sgu(source_engine);raw=response();enqueue(source_engine,BINDING.source_id,now=raw.fetched_at)
    started,release=Event(),Event()
    def fetch(*_,**__):
        started.set()
        if not release.wait(timeout=10):raise RuntimeError('Fetch gate timed out')
        return raw
    app=create_app(Settings(database_url=source_engine.url.render_as_string(hide_password=False),auto_create_schema=False))
    with ThreadPoolExecutor(max_workers=1) as pool:
        future=pool.submit(run_once,source_engine,RawStore(tmp_path/'raw'),registry=Registry((make_adapter(KEY),)),fetch=fetch,now=lambda:raw.fetched_at)
        try:
            assert started.wait(timeout=5)
            with TestClient(app) as client:
                assert client.get('/api/health').status_code==200
                assert client.post('/api/v1/session',headers=HEADERS).status_code==204
                assert client.get('/api/v1/watches').json()==[]
                assert client.get('/api/v1/universities').status_code==200
        finally:release.set()
        assert future.result(timeout=10)['state']=='success'
