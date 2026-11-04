import pytest
from app.config import Settings


@pytest.mark.parametrize('name,value',[('ENVIRONMENT','prod'),('SECURE_COOKIE','yes'),('AUTO_CREATE_SCHEMA','1')])
def test_invalid_environment_values_do_not_fall_back_to_development(monkeypatch,name,value):
    monkeypatch.setenv(name,value)
    with pytest.raises(RuntimeError): Settings.from_env()


def test_direct_settings_cannot_bypass_production_guards():
    valid=dict(environment='production',database_url='postgresql+psycopg://test:test@localhost/test',secure_cookie=True,auto_create_schema=False,allowed_hosts=('example.org',),public_origin='https://example.org')
    assert Settings(**valid).secure_cookie
    for changes in [dict(database_url='sqlite://'),dict(secure_cookie=False),dict(auto_create_schema=True)]:
        with pytest.raises(RuntimeError): Settings(**(valid|changes))


def test_api_description_is_not_served_in_production(tmp_path):
    from fastapi.testclient import TestClient
    from app.main import create_app
    from app.config import Settings
    production=Settings(database_url='postgresql+psycopg://user:pass@127.0.0.1:1/never',environment='production',secure_cookie=True,auto_create_schema=False,allowed_hosts=('example.org',),public_origin='https://example.org')
    app=create_app(production)
    assert app.docs_url is None and app.openapi_url is None
    development=create_app(Settings(database_url=f'sqlite:///{tmp_path}/dev.db'))
    assert development.docs_url=='/api/docs'
