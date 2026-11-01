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
