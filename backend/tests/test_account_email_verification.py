from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from threading import Barrier

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.account_security import credential_digest, new_token
from app.accounts import AccountActionToken, AccountSession, AccountUser
from account_support import HEADERS, PASSWORD, auth_app, auth_client, csrf, postgres_engine, register  # noqa: F401
from test_account_login import login
from fastapi.testclient import TestClient

pytestmark = pytest.mark.postgres


def request_verification(client, email='person@example.org', headers=None):
    return client.post('/api/v1/auth/verification/request', json=dict(email=email), headers=headers or csrf(client))


def confirm(client, token, headers=None):
    return client.post('/api/v1/auth/verification/confirm', json=dict(token=token), headers=headers or csrf(client))


def registered(client, app):
    assert register(client).status_code == 202
    return app.state.test_mailer.deliveries[-1][1]


def test_real_register_confirm_then_login_and_token_once(auth_client, auth_app):
    token = registered(auth_client, auth_app)
    assert login(auth_client).status_code == 401
    result = confirm(auth_client, token)
    assert result.status_code == 204 and result.content == b'' and 'set-cookie' not in result.headers
    with Session(auth_app.state.engine) as db:
        user = db.scalar(select(AccountUser)); action = db.get(AccountActionToken, credential_digest('verify_email', token))
        assert user.email_verified_at is not None and action.used_at is not None
        assert db.scalar(select(func.count()).select_from(AccountSession)) == 0
    assert confirm(auth_client, token).status_code == 400
    assert login(auth_client).status_code == 200


def test_resend_invalidates_older_links_and_preserves_password(auth_client, auth_app):
    old = registered(auth_client, auth_app)
    with Session(auth_app.state.engine) as db: before = db.scalar(select(AccountUser.password_hash))
    assert request_verification(auth_client).status_code == 202
    current = auth_app.state.test_mailer.verification_deliveries[-1][1]
    assert current != old and confirm(auth_client, old).status_code == 400
    with Session(auth_app.state.engine) as db:
        assert db.scalar(select(AccountUser.password_hash)) == before
        assert db.scalar(select(AccountUser)).email_verified_at is None
        action = db.get(AccountActionToken, credential_digest('verify_email', current))
        assert action.expires_at-action.created_at == timedelta(hours=24)
    assert confirm(auth_client, current).status_code == 204


@pytest.mark.parametrize('kind', ['missing', 'verified', 'disabled'])
def test_ineligible_requests_use_same_public_response_and_delivery_path(auth_client, auth_app, kind):
    if kind != 'missing':
        registered(auth_client, auth_app)
        with Session(auth_app.state.engine) as db:
            user = db.scalar(select(AccountUser))
            if kind == 'verified': user.email_verified_at = datetime.now(timezone.utc)
            else: user.status = 'disabled'
            db.commit()
    response = request_verification(auth_client)
    assert response.status_code == 202
    assert response.json() == dict(message='Запрос принят. Если операция доступна для этого адреса, проверьте почту.')
    assert auth_app.state.test_mailer.verification_deliveries[-1] == ('person@example.org', None)


@pytest.mark.parametrize('kind', ['forged', 'expired', 'used', 'wrong_purpose', 'deleted', 'disabled'])
def test_invalid_confirmation_is_uniform_and_never_confirms(auth_client, auth_app, kind):
    token = registered(auth_client, auth_app)
    with Session(auth_app.state.engine) as db:
        action = db.scalar(select(AccountActionToken)); user = db.scalar(select(AccountUser)); now = datetime.now(timezone.utc)
        if kind == 'expired': action.created_at = now-timedelta(days=2); action.expires_at = now-timedelta(days=1)
        elif kind == 'used': action.used_at = now
        elif kind == 'wrong_purpose':
            action.purpose = 'reset_password'; action.token_hash = credential_digest('reset_password', token)
        elif kind == 'deleted': db.delete(user)
        elif kind == 'disabled': user.status = 'disabled'
        db.commit()
    if kind == 'forged': token = new_token()
    response = confirm(auth_client, token)
    assert response.status_code == 400 and response.json()['code'] == 'invalid_token'
    assert token not in response.text and PASSWORD not in response.text
    with Session(auth_app.state.engine) as db:
        assert all(u.email_verified_at is None for u in db.scalars(select(AccountUser)))


def test_concurrent_confirmation_consumes_one_token(auth_client, auth_app):
    token = registered(auth_client, auth_app); barrier = Barrier(2)
    def attempt(_):
        with TestClient(auth_app) as client:
            headers = csrf(client); barrier.wait(timeout=10)
            return confirm(client, token, headers).status_code
    with ThreadPoolExecutor(2) as pool: assert sorted(pool.map(attempt, range(2))) == [204, 400]
    with Session(auth_app.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(AccountSession)) == 0


def test_concurrent_resend_leaves_only_latest_action_usable(auth_client, auth_app):
    registered(auth_client, auth_app); barrier = Barrier(2)
    def attempt(_):
        with TestClient(auth_app) as client:
            headers = csrf(client); barrier.wait(timeout=10)
            return request_verification(client, headers=headers).status_code
    with ThreadPoolExecutor(2) as pool: assert list(pool.map(attempt, range(2))) == [202, 202]
    tokens = [token for _, token in auth_app.state.test_mailer.verification_deliveries]
    assert len(tokens) == 2
    outcomes = [confirm(auth_client, token).status_code for token in tokens]
    assert sorted(outcomes) == [204, 400]


def test_unavailable_and_failed_provider_never_claim_confirmation(auth_client, auth_app, postgres_engine):
    from app.config import Settings
    from app.main import create_app
    registered(auth_client, auth_app)
    auth_app.state.test_mailer.fail = True
    assert request_verification(auth_client).status_code == 503
    assert request_verification(auth_client, email='unknown@example.org').status_code == 503
    with Session(auth_app.state.engine) as db: assert db.scalar(select(AccountUser)).email_verified_at is None
    app = create_app(Settings(database_url=postgres_engine.url.render_as_string(hide_password=False), auto_create_schema=False,
                             auth_enabled=True, auth_rate_key='isolated-test-key-with-at-least-32-bytes'))
    with TestClient(app) as client:
        assert request_verification(client).status_code == 503
        assert request_verification(client, email='missing@example.org').status_code == 503


def test_provider_outage_does_not_block_confirming_already_delivered_link(auth_client, auth_app):
    token = registered(auth_client, auth_app)
    auth_app.state.test_mailer.fail = True
    assert confirm(auth_client, token).status_code == 204
