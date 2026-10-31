import pytest

from app.config import Settings


def test_development_defaults(monkeypatch):
    for key in ('ENVIRONMENT', 'DATABASE_URL', 'SECURE_COOKIE', 'AUTO_CREATE_SCHEMA'):
        monkeypatch.delenv(key, raising=False)
    assert Settings.from_env() == Settings()


def test_production_requires_postgres(monkeypatch):
    monkeypatch.setenv('ENVIRONMENT', 'production')
    monkeypatch.setenv('DATABASE_URL', 'sqlite:///./test.db')
    with pytest.raises(RuntimeError):
        Settings.from_env()


def test_production_disables_schema_creation(monkeypatch):
    monkeypatch.setenv('ENVIRONMENT', 'production')
    monkeypatch.setenv('DATABASE_URL', 'postgresql+psycopg://example:example@localhost/example')
    monkeypatch.setenv('SECURE_COOKIE', 'true')
    monkeypatch.setenv('AUTO_CREATE_SCHEMA', 'true')
    config = Settings.from_env()
    assert config.secure_cookie is True
    assert config.auto_create_schema is False
