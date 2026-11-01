import pytest
pytest_plugins = ['pg_guard']
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def application(tmp_path):
    return create_app(Settings(database_url=f"sqlite:///{tmp_path / 'test.db'}"))


@pytest.fixture
def client(application):
    # Lifespan creates a separate temporary DB for every test.
    with TestClient(application) as client:
        yield client


@pytest.fixture
def source_engine(tmp_path):
    from app.database import Base, make_engine
    engine = make_engine(f"sqlite:///{tmp_path / 'sources.db'}")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()
