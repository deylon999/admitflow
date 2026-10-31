import pytest
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
