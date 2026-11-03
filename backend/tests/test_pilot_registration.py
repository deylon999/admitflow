from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import func,select
from sqlalchemy.orm import Session

from app.admissions import CompetitionGroup,Source
from app.sources.adapters.sgu2026 import SOURCE_ID,make_adapter
from app.sources.contracts import AdapterError
from app.sources.pilots import register_sgu
from app.sources.registry import Registry
from test_sgu_adapter import KEY


def test_registration_is_explicit_disabled_and_idempotent(source_engine):
    with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(lambda _:register_sgu(source_engine),range(8)))
    assert sum(row['created'] for row in results)==1
    assert all(row['enabled'] is False and row['kind']=='archive' for row in results)
    with Session(source_engine) as db:
        assert db.scalar(select(func.count()).select_from(Source))==1
        assert db.get(CompetitionGroup,SOURCE_ID).coverage=='candidate'


def test_enable_requires_attested_key_and_conflicting_metadata_is_not_overwritten(source_engine):
    with pytest.raises(AdapterError,match='adapter_unavailable'):register_sgu(source_engine,enable=True)
    with Session(source_engine) as db:assert db.scalar(select(func.count()).select_from(Source))==0
    registry=Registry((make_adapter(KEY),))
    assert register_sgu(source_engine,enable=True,registry=registry)['enabled'] is True
    with Session(source_engine) as db:
        db.get(CompetitionGroup,SOURCE_ID).seats=99;db.commit()
    with pytest.raises(AdapterError,match='invalid_binding'):register_sgu(source_engine,registry=registry)
    with Session(source_engine) as db:assert db.get(CompetitionGroup,SOURCE_ID).seats==99


def test_api_reports_configured_archive_adapter_without_claiming_assessment(monkeypatch,tmp_path):
    from fastapi.testclient import TestClient
    from app.config import Settings
    from app.main import create_app
    monkeypatch.setenv('SOURCE_IDENTITY_KEY',KEY.hex())
    app=create_app(Settings(database_url=f'sqlite:///{tmp_path}/api.db'))
    with TestClient(app) as client:
        assert client.get('/api/v1/coverage').json()['automaticSources']==0
        register_sgu(app.state.engine,enable=True,registry=app.state.source_registry)
        status=client.get(f'/api/v1/sources/{SOURCE_ID}/status').json()
        assert status['adapterAvailable'] is True and status['dataKind']=='archive'
        assert status['assessmentAvailable'] is False and status['publishedSnapshotId'] is None
