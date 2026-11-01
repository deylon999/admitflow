import pytest

from app.config import Settings


def test_development_defaults(monkeypatch):
    for key in ('ENVIRONMENT', 'DATABASE_URL', 'SECURE_COOKIE', 'AUTO_CREATE_SCHEMA', 'ALLOWED_HOSTS', 'PUBLIC_ORIGIN'):
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
    monkeypatch.setenv('ALLOWED_HOSTS','admitflow.example')
    monkeypatch.setenv('PUBLIC_ORIGIN','https://admitflow.example')
    config = Settings.from_env()
    assert config.secure_cookie is True
    assert config.auto_create_schema is False


def test_production_origin_and_host_must_be_explicit(monkeypatch):
    monkeypatch.setenv('ENVIRONMENT','production')
    monkeypatch.setenv('DATABASE_URL','postgresql+psycopg://example:example@localhost/example')
    monkeypatch.delenv('ALLOWED_HOSTS',raising=False)
    monkeypatch.delenv('PUBLIC_ORIGIN',raising=False)
    with pytest.raises(RuntimeError):
        Settings.from_env()
    for host,origin in [('*','https://example.org'),('example.org','http://example.org'),('example.org','https://other.org'),('example.org','https://example.org/path')]:
        with pytest.raises(RuntimeError):
            Settings(environment='production',allowed_hosts=(host,),public_origin=origin)
