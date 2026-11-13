import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from threading import Barrier

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.account_api import CSRF_COOKIE
from app.account_security import credential_digest, verify_password
from app.accounts import AccountActionToken, AccountCsrfContext, AccountRateBucket, AccountSession, AccountUser
from app.config import Settings
from app.main import create_app
from account_support import HEADERS, KEY, PASSWORD, auth_app, auth_client, csrf, postgres_engine, register  # noqa: F401

pytestmark = pytest.mark.postgres


def test_real_registration_hash_action_and_generic_duplicate(auth_client, auth_app):
    headers = csrf(auth_client)
    response = register(auth_client, ' PERSON@Example.ORG ', headers=headers)
    assert response.status_code == 202
    assert response.json() == register(auth_client, 'person@example.org', headers=headers).json()
    assert 'admitflow_access' not in response.headers.get('set-cookie', '')
    with Session(auth_app.state.engine) as db:
        user = db.scalar(select(AccountUser))
        assert user.email == 'person@example.org' and user.email_verified_at is None
        assert verify_password(PASSWORD, user.password_hash).valid
        action = db.scalar(select(AccountActionToken))
        token = auth_app.state.test_mailer.deliveries[0][1]
        assert action.token_hash == credential_digest('verify_email', token)
        assert action.purpose == 'verify_email' and action.used_at is None
        assert action.expires_at-action.created_at == timedelta(hours=24)
        assert db.scalar(select(func.count()).select_from(AccountSession)) == 0
        assert db.scalar(select(func.count()).select_from(AccountUser)) == 1
        original_hash = user.password_hash
    assert auth_app.state.test_mailer.deliveries[1] == ('person@example.org', None)
    assert token not in response.text and original_hash not in response.text


@pytest.mark.parametrize('operation', ['register', 'login'])
@pytest.mark.parametrize('kind', ['missing', 'wrong', 'other_context', 'expired', 'origin', 'cross_site', 'write_header'])
def test_auth_write_csrf_and_origin_fail_closed(auth_client, auth_app, kind, operation):
    headers = csrf(auth_client)
    if kind == 'missing': headers.pop('X-CSRF-Token')
    elif kind == 'wrong': headers['X-CSRF-Token'] = 'x'*43
    elif kind == 'other_context':
        with TestClient(auth_app, client=('192.0.2.2', 5000)) as other:
            headers['X-CSRF-Token'] = csrf(other)['X-CSRF-Token']
    elif kind == 'expired':
        with Session(auth_app.state.engine) as db:
            context = db.scalar(select(AccountCsrfContext))
            context.created_at = datetime.now(timezone.utc)-timedelta(hours=2)
            context.expires_at = datetime.now(timezone.utc)-timedelta(hours=1); db.commit()
    elif kind == 'origin': headers['Origin'] = 'http://evil.example'
    elif kind == 'cross_site': headers['Sec-Fetch-Site'] = 'cross-site'
    else: headers.pop('X-Requested-With')
    response = auth_client.post('/api/v1/auth/'+operation, headers=headers,
                                json=dict(email='person@example.org', password=PASSWORD))
    assert response.status_code == 403
    with Session(auth_app.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(AccountUser)) == 0
    assert auth_app.state.test_mailer.deliveries == []


@pytest.mark.parametrize('patch', [{'email':'bad'}, {'password':'short'}, {'password':'x'*129},
                                 {'password':5}, {'email':5}, {'password':'x'*20+'\ud800'}, {'unexpected':True}])
def test_invalid_payload_is_redacted_and_never_persisted(auth_client, auth_app, patch):
    body = dict(email='private-marker@example.org', password=PASSWORD) | patch
    response = auth_client.post('/api/v1/auth/register', content=json.dumps(body),
                                headers=csrf(auth_client) | {'Content-Type': 'application/json'})
    assert response.status_code == 422
    assert PASSWORD not in response.text and 'private-marker' not in response.text
    assert auth_app.state.test_mailer.deliveries == []


def test_missing_mail_port_is_explicit_for_every_email(auth_app, postgres_engine):
    config = Settings(database_url=postgres_engine.url.render_as_string(hide_password=False), auto_create_schema=False,
                      auth_enabled=True, auth_rate_key=KEY)
    with TestClient(create_app(config)) as client:
        first = register(client)
        second = register(client, 'missing@example.org')
        assert first.status_code == second.status_code == 503 and first.json() == second.json()
    with Session(postgres_engine) as db:
        assert db.scalar(select(func.count()).select_from(AccountUser)) == 0


def test_provider_failure_never_claims_success_or_confirms_email(auth_client, auth_app, caplog):
    auth_app.state.test_mailer.fail = True
    first = register(auth_client)
    duplicate = register(auth_client)
    assert first.status_code == duplicate.status_code == 503 and first.json() == duplicate.json()
    assert 'private details' not in first.text and PASSWORD not in caplog.text
    with Session(auth_app.state.engine) as db:
        assert db.scalar(select(AccountUser)).email_verified_at is None
        assert db.scalar(select(func.count()).select_from(AccountSession)) == 0


def test_concurrent_registration_creates_one_user_and_action(auth_app):
    barrier = Barrier(2)
    def attempt(index):
        with TestClient(auth_app, client=(f'192.0.2.{index+1}', 5000)) as client:
            headers = csrf(client); barrier.wait(timeout=10)
            return register(client, headers=headers)
    with ThreadPoolExecutor(2) as pool:
        responses = list(pool.map(attempt, range(2)))
    assert [r.status_code for r in responses] == [202, 202]
    assert responses[0].json() == responses[1].json()
    with Session(auth_app.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(AccountUser)) == 1
        assert db.scalar(select(func.count()).select_from(AccountActionToken)) == 1
    assert sum(token is not None for _, token in auth_app.state.test_mailer.deliveries) == 1


def test_email_mail_budget_is_uniform_and_persistent(auth_client, auth_app):
    headers = csrf(auth_client)
    assert all(register(auth_client, headers=headers).status_code == 202 for _ in range(4))
    assert len(auth_app.state.test_mailer.deliveries) == 3
    with Session(auth_app.state.engine) as db:
        bucket = db.scalar(select(AccountRateBucket).where(AccountRateBucket.operation == 'register-email'))
        assert bucket.used == 3 and 'person' not in bucket.subject_hash


def test_csrf_bootstrap_requires_same_origin_header_and_does_not_use_guest(auth_client):
    assert auth_client.get('/api/v1/auth/csrf').status_code == 403
    assert auth_client.get('/api/v1/auth/csrf', headers=HEADERS | {'Origin':'http://evil.example'}).status_code == 403
    response = auth_client.get('/api/v1/auth/csrf', headers=HEADERS)
    assert response.status_code == 200
    cookie = response.headers['set-cookie']
    assert CSRF_COOKIE in cookie and 'HttpOnly' in cookie and 'Path=/api/v1' in cookie and 'SameSite=lax' in cookie
    assert 'Domain=' not in cookie
    assert 'abiturient_session' not in auth_client.cookies


def test_registration_commit_failure_rolls_back_and_never_sends(auth_client, auth_app, monkeypatch):
    from sqlalchemy.exc import SQLAlchemyError
    headers = csrf(auth_client)
    original = Session.commit
    def fail_user_transaction(db):
        if any(isinstance(obj, AccountActionToken) for obj in db.new):
            raise SQLAlchemyError('private insert failure')
        return original(db)
    monkeypatch.setattr(Session, 'commit', fail_user_transaction)
    response = register(auth_client, headers=headers)
    assert response.status_code == 503 and 'private insert' not in response.text
    assert auth_app.state.test_mailer.deliveries == []
    with Session(auth_app.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(AccountUser)) == 0
        assert db.scalar(select(func.count()).select_from(AccountActionToken)) == 0
        assert db.scalar(select(AccountRateBucket).where(AccountRateBucket.operation == 'register-email')).used == 1
