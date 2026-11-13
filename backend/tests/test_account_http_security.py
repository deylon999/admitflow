from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.account_api import ACCESS_COOKIE
from app.accounts import AccountSession, AccountUser
from app.config import Settings
from app.main import create_app
from account_support import HEADERS, KEY, PASSWORD, RecordingMailer, auth_app, auth_client, csrf, postgres_engine, register  # noqa: F401
from test_account_login import login, verified

pytestmark = pytest.mark.postgres


def test_disabled_default_is_explicit_without_mutating_guest_or_accounts(postgres_engine):
    app = create_app(Settings(database_url=postgres_engine.url.render_as_string(hide_password=False), auto_create_schema=False))
    with TestClient(app) as client:
        assert client.post('/api/v1/session', headers=HEADERS).status_code == 204
        payloads = {
            'register': {'email':'private@example.org','password':PASSWORD},
            'login': {'email':'private@example.org','password':PASSWORD},
            'verification/request': {'email':'private@example.org'},
            'recovery/request': {'email':'private@example.org'},
            'verification/confirm': {'token':'x'*43},
            'recovery/confirm': {'token':'x'*43,'password':PASSWORD},
        }
        for path, method in [('csrf', 'GET'), ('register', 'POST'), ('login', 'POST'), ('session', 'GET'),
                             ('refresh', 'POST'), ('logout', 'POST'), ('verification/request','POST'),
                             ('verification/confirm','POST'), ('recovery/request','POST'), ('recovery/confirm','POST')]:
            response = client.request(method, '/api/v1/auth/'+path, headers=HEADERS,
                                      json=payloads.get(path,{}) if method=='POST' else None)
            assert response.status_code == 503 and response.json()['code'] == 'auth_unavailable'
        assert client.get('/api/v1/session').status_code == 200
    with Session(postgres_engine) as db:
        assert db.scalar(select(func.count()).select_from(AccountUser)) == 0


def test_production_cookies_are_secure_httponly_host_only(postgres_engine):
    config = Settings(database_url=postgres_engine.url.render_as_string(hide_password=False), environment='production',
                      secure_cookie=True, auto_create_schema=False, allowed_hosts=('example.org',),
                      public_origin='https://example.org', auth_enabled=True, auth_rate_key=KEY)
    app = create_app(config, registration_mailer=RecordingMailer())
    headers = {'X-Requested-With':'abiturient', 'Origin':'https://example.org'}
    with TestClient(app, base_url='https://example.org') as client:
        response = client.get('/api/v1/auth/csrf', headers=headers)
        assert 'Secure' in response.headers['set-cookie'] and 'HttpOnly' in response.headers['set-cookie']
        headers['X-CSRF-Token'] = response.json()['csrfToken']
        assert client.post('/api/v1/auth/register', headers=headers, json=dict(email='person@example.org',password=PASSWORD)).status_code == 202
        with Session(postgres_engine) as db:
            db.scalar(select(AccountUser)).email_verified_at = datetime.now(timezone.utc); db.commit()
        result = client.post('/api/v1/auth/login', headers=headers, json=dict(email='person@example.org',password=PASSWORD))
        assert result.status_code == 200
        assert all('Secure' in c and 'HttpOnly' in c and 'SameSite=lax' in c and 'Path=/api/v1' in c and 'Domain=' not in c
                   for c in result.headers.get_list('set-cookie'))
        assert 'admitflow_refresh' in client.cookies
        assert any('admitflow_refresh=' in c and 'Path=/api/v1/auth' in c for c in result.headers.get_list('set-cookie'))
        assert client.get('/api/v1/auth/session').status_code == 200


def test_auth_logs_and_response_never_include_password_or_credentials(auth_client, auth_app, caplog):
    verified(auth_client, auth_app); response = login(auth_client)
    assert response.status_code == 200
    token = auth_client.cookies.get(ACCESS_COOKIE)
    mail_token = auth_app.state.test_mailer.deliveries[0][1]
    headers = csrf(auth_client)
    assert login(auth_client, password='wrong password marker', headers=headers).status_code == 401
    for secret in [PASSWORD, token, mail_token, headers['X-CSRF-Token'], 'wrong password marker', 'person@example.org']:
        assert secret not in caplog.text
    assert token not in response.text and mail_token not in response.text


def test_commit_failure_never_sets_session_cookie(auth_client, auth_app, monkeypatch):
    from sqlalchemy.exc import SQLAlchemyError
    verified(auth_client, auth_app); headers = csrf(auth_client)
    original = Session.commit
    def fail_for_credentials(db):
        if any(isinstance(obj, AccountSession) for obj in db.identity_map.values()):
            raise SQLAlchemyError('private database details')
        return original(db)
    monkeypatch.setattr(Session, 'commit', fail_for_credentials)
    response = login(auth_client, headers=headers)
    assert response.status_code == 503 and 'private database' not in response.text
    assert ACCESS_COOKIE not in auth_client.cookies
    with Session(auth_app.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(AccountSession)) == 0


def test_auth_config_requires_stable_secret_and_hides_it(monkeypatch):
    assert not Settings().auth_enabled
    for key in [None, '', 'short']:
        with pytest.raises(RuntimeError): Settings(auth_enabled=True, auth_rate_key=key)
    assert KEY not in repr(Settings(auth_enabled=True, auth_rate_key=KEY))
    monkeypatch.setenv('AUTH_ENABLED','true'); monkeypatch.setenv('AUTH_RATE_KEY',KEY)
    assert Settings.from_env().auth_rate_key == KEY
    monkeypatch.setenv('AUTH_ENABLED','yes')
    with pytest.raises(RuntimeError): Settings.from_env()


def test_temporary_database_failure_is_503_not_missing_account(auth_client, auth_app, monkeypatch):
    from app import account_api
    from sqlalchemy.exc import SQLAlchemyError
    verified(auth_client, auth_app); assert login(auth_client).status_code == 200
    access = auth_client.cookies.get(ACCESS_COOKIE)
    def fail_read(*args): raise SQLAlchemyError('private backend failure')
    monkeypatch.setattr(account_api, 'current_account', fail_read)
    response = auth_client.get('/api/v1/auth/session')
    assert response.status_code == 503 and response.json()['code'] == 'auth_unavailable'
    assert 'private backend' not in response.text
    assert auth_client.cookies.get(ACCESS_COOKIE) == access
