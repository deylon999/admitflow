from datetime import datetime, timezone
from urllib.parse import parse_qs, urlsplit

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import account_api, account_mail
from app.account_limits import Budget, consume_budgets
from app.account_security import credential_digest
from app.accounts import AccountActionToken, AccountCsrfContext, AccountSession, AccountUser
from app.config import Settings
from app.main import create_app
from account_support import HEADERS, KEY, PASSWORD, auth_app, auth_client, csrf, postgres_engine  # noqa: F401
from test_account_email_verification import confirm, registered, request_verification
from test_account_recovery import NEW_PASSWORD, recoverable, request_recovery, reset
from test_account_mail import BASE, FakeSMTP

pytestmark = pytest.mark.postgres


@pytest.mark.parametrize('operation', ['verification/request', 'verification/confirm', 'recovery/request', 'recovery/confirm'])
@pytest.mark.parametrize('kind', ['missing', 'wrong', 'foreign', 'expired', 'origin', 'cross_site', 'write_header'])
def test_action_endpoints_reject_csrf_origin_and_headers_without_changes(auth_client, auth_app, operation, kind):
    token = recoverable(auth_client, auth_app) if operation.startswith('recovery') else registered(auth_client, auth_app)
    headers = csrf(auth_client)
    with Session(auth_app.state.engine) as db:
        original_hash = db.scalar(select(AccountUser.password_hash))
        before = [(a.token_hash,a.used_at) for a in db.scalars(select(AccountActionToken).order_by(AccountActionToken.token_hash))]
    if kind == 'missing': headers.pop('X-CSRF-Token')
    elif kind == 'wrong': headers['X-CSRF-Token'] = 'x'*43
    elif kind == 'foreign':
        with TestClient(auth_app) as other: headers['X-CSRF-Token'] = csrf(other)['X-CSRF-Token']
    elif kind == 'expired':
        from datetime import timedelta
        with Session(auth_app.state.engine) as db:
            ctx = db.scalar(select(AccountCsrfContext)); now = datetime.now(timezone.utc)
            ctx.created_at = now-timedelta(hours=2); ctx.expires_at = now-timedelta(hours=1); db.commit()
    elif kind == 'origin': headers['Origin'] = 'http://evil.example'
    elif kind == 'cross_site': headers['Sec-Fetch-Site'] = 'cross-site'
    else: headers.pop('X-Requested-With')
    body = dict(email='person@example.org') if operation.endswith('/request') else dict(token=token)
    if operation == 'recovery/confirm': body['password'] = NEW_PASSWORD
    response = auth_client.post('/api/v1/auth/'+operation, json=body, headers=headers)
    assert response.status_code == 403 and 'set-cookie' not in response.headers
    with Session(auth_app.state.engine) as db:
        assert db.scalar(select(AccountUser.password_hash)) == original_hash
        assert [(a.token_hash,a.used_at) for a in db.scalars(select(AccountActionToken).order_by(AccountActionToken.token_hash))] == before


@pytest.mark.parametrize('purpose', ['verify_email', 'reset_password'])
def test_attempt_budget_is_durable_without_revealing_token(auth_client, auth_app, purpose):
    token = recoverable(auth_client, auth_app) if purpose=='reset_password' else registered(auth_client, auth_app)
    headers = csrf(auth_client)
    with Session(auth_app.state.engine) as db:
        db.get(AccountActionToken, credential_digest(purpose, token)).used_at = datetime.now(timezone.utc); db.commit()
    operation = reset if purpose=='reset_password' else confirm
    results = [operation(auth_client, token, headers=headers) for _ in range(11)]
    assert [r.status_code for r in results] == [400]*10+[429]
    assert 1 <= int(results[-1].headers['retry-after']) <= 900
    assert all(token not in r.text for r in results)


def test_email_budget_is_shared_by_register_verify_and_recovery(auth_client, auth_app):
    registered(auth_client, auth_app)  # First mail.
    assert request_verification(auth_client).status_code == 202  # Second mail.
    token = auth_app.state.test_mailer.verification_deliveries[-1][1]
    assert request_recovery(auth_client).status_code == 202  # Third, generic notice (unverified).
    assert request_verification(auth_client).status_code == 202  # Suppressed, no false delivery claim.
    assert len(auth_app.state.test_mailer.deliveries)+len(auth_app.state.test_mailer.verification_deliveries)+len(auth_app.state.test_mailer.recovery_deliveries) == 3
    assert confirm(auth_client, token).status_code == 204  # Suppressed request did not retire the valid link.


def test_shared_mail_peer_budget_ignores_forwarding_headers(auth_client, auth_app, monkeypatch):
    fixed = datetime.now(timezone.utc)
    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None): return fixed
    monkeypatch.setattr(account_api, 'datetime', FixedDateTime)
    headers = csrf(auth_client)
    rule = Budget('mail-peer', ('peer','192.0.2.1'), 20, 3600)
    for _ in range(20): consume_budgets(auth_app.state.engine, KEY, [rule], now=fixed)
    result = request_recovery(auth_client, email='unknown@example.org', headers=headers | {'X-Forwarded-For':'203.0.113.9'})
    assert result.status_code == 429 and 'retry-after' in result.headers
    assert auth_app.state.test_mailer.recovery_deliveries == []


@pytest.mark.parametrize('purpose', ['verify_email','reset_password'])
def test_failed_issuance_preserves_older_link_and_does_not_send(auth_client, auth_app, monkeypatch, purpose):
    from sqlalchemy.exc import SQLAlchemyError
    token = recoverable(auth_client, auth_app) if purpose=='reset_password' else registered(auth_client, auth_app)
    original = Session.commit
    def fail_new_action(db):
        if any(isinstance(obj, AccountActionToken) for obj in db.new): raise SQLAlchemyError('private action failure')
        return original(db)
    with monkeypatch.context() as patch:
        patch.setattr(Session,'commit',fail_new_action)
        response = request_recovery(auth_client) if purpose=='reset_password' else request_verification(auth_client)
        assert response.status_code == 503 and 'private action' not in response.text
    with Session(auth_app.state.engine) as db:
        assert db.get(AccountActionToken, credential_digest(purpose, token)).used_at is None
    operation = reset if purpose=='reset_password' else confirm
    assert operation(auth_client, token).status_code == 204


def test_failed_verification_commit_keeps_email_and_action_unmodified(auth_client, auth_app, monkeypatch):
    from sqlalchemy.exc import SQLAlchemyError
    token = registered(auth_client, auth_app); original = Session.commit
    def fail_confirmation(db):
        if any(isinstance(obj,AccountUser) and obj.email_verified_at is not None for obj in db.identity_map.values()):
            raise SQLAlchemyError('private confirmation failure')
        return original(db)
    with monkeypatch.context() as patch:
        patch.setattr(Session,'commit',fail_confirmation)
        assert confirm(auth_client,token).status_code == 503
    with Session(auth_app.state.engine) as db:
        assert db.scalar(select(AccountUser)).email_verified_at is None
        assert db.get(AccountActionToken,credential_digest('verify_email',token)).used_at is None
    assert confirm(auth_client,token).status_code == 204


def test_previously_delivered_recovery_can_confirm_without_configured_transport(auth_client, auth_app, postgres_engine):
    token = recoverable(auth_client,auth_app)
    app = create_app(Settings(database_url=postgres_engine.url.render_as_string(hide_password=False),
                             auto_create_schema=False,auth_enabled=True,auth_rate_key=KEY))
    with TestClient(app) as browser:
        assert request_recovery(browser).status_code == 503
        assert request_recovery(browser,email='missing@example.org').status_code == 503
        assert reset(browser,token).status_code == 204


def test_action_secrets_and_passwords_never_appear_in_http_logs(auth_client,auth_app,caplog):
    token = recoverable(auth_client,auth_app); headers = csrf(auth_client)
    response = reset(auth_client,token,headers=headers)
    assert response.status_code == 204
    for secret in (token, PASSWORD, NEW_PASSWORD, headers['X-CSRF-Token'], 'person@example.org'):
        assert secret not in caplog.text and secret not in response.text


@pytest.mark.parametrize('operation', ['verification/confirm','recovery/confirm'])
def test_malformed_secret_and_callback_are_rejected_without_echo(auth_client,auth_app,operation):
    token = registered(auth_client,auth_app)
    body = dict(token=token, callbackUrl='https://evil.example/steal')
    if operation.startswith('recovery'): body['password'] = NEW_PASSWORD
    response = auth_client.post('/api/v1/auth/'+operation,json=body,headers=csrf(auth_client))
    assert response.status_code == 422 and token not in response.text and 'evil.example' not in response.text


def test_api_to_smtp_adapter_verification_recovery_flow_with_isolated_protocol_client(postgres_engine,monkeypatch):
    clients=[]
    def connect(*args,**kwargs):
        smtp=FakeSMTP(); clients.append(smtp); return smtp
    monkeypatch.setattr(account_mail.smtplib,'SMTP',connect)
    config=Settings(**(BASE | dict(database_url=postgres_engine.url.render_as_string(hide_password=False),
                                 auto_create_schema=False,auth_enabled=True,auth_rate_key=KEY)))
    app=create_app(config)  # Actual configured SMTP factory, no injected recording port.
    base_headers={'X-Requested-With':'abiturient','Origin':'https://example.org'}
    def headers(browser):
        return base_headers | {'X-CSRF-Token':browser.get('/api/v1/auth/csrf',headers=base_headers).json()['csrfToken']}
    def delivered_token():
        text=clients[-1].messages[0][0].get_content()
        url=next(line for line in text.splitlines() if line.startswith('https://'))
        assert urlsplit(url).netloc == 'example.org' and not urlsplit(url).query
        return parse_qs(urlsplit(url).fragment)['token'][0]
    with TestClient(app,base_url='https://example.org') as browser:
        assert browser.post('/api/v1/auth/register',json=dict(email='person@example.org',password=PASSWORD),headers=headers(browser)).status_code == 202
        verification=delivered_token()
        assert browser.post('/api/v1/auth/verification/confirm',json=dict(token=verification),headers=headers(browser)).status_code == 204
        assert browser.post('/api/v1/auth/login',json=dict(email='person@example.org',password=PASSWORD),headers=headers(browser)).status_code == 200
        assert browser.post('/api/v1/auth/recovery/request',json=dict(email='person@example.org'),headers=headers(browser)).status_code == 202
        recovery=delivered_token()
        with TestClient(app,base_url='https://example.org') as anonymous:
            assert anonymous.post('/api/v1/auth/recovery/confirm',json=dict(token=recovery,password=NEW_PASSWORD),headers=headers(anonymous)).status_code == 204
        assert browser.get('/api/v1/auth/session').status_code == 401
        assert browser.post('/api/v1/auth/login',json=dict(email='person@example.org',password=NEW_PASSWORD),headers=headers(browser)).status_code == 200
    assert len(clients)==2
    assert all(PASSWORD not in client.messages[0][0].get_content() and NEW_PASSWORD not in client.messages[0][0].get_content() for client in clients)


@pytest.mark.parametrize('operation', ['verification/confirm','recovery/confirm'])
@pytest.mark.parametrize('token', ['x'*42, 'x'*44, None, 123, '!'*43])
def test_malformed_action_token_is_bounded_and_not_echoed(auth_client,auth_app,operation,token):
    body=dict(token=token)
    if operation.startswith('recovery'): body['password']=NEW_PASSWORD
    response=auth_client.post('/api/v1/auth/'+operation,json=body,headers=csrf(auth_client))
    assert response.status_code == 422
    if isinstance(token,str): assert token not in response.text
    assert NEW_PASSWORD not in response.text
    with Session(auth_app.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(AccountUser)) == 0
        assert db.scalar(select(func.count()).select_from(AccountActionToken)) == 0
