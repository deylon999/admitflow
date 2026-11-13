from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from threading import Barrier, Event

import pytest
from fastapi.testclient import TestClient
from httpx import Cookies
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import account_actions, account_api
from app.account_security import credential_digest, new_token, verify_password
from app.accounts import AccountActionToken, AccountSession, AccountUser
from account_support import HEADERS, PASSWORD, auth_app, auth_client, csrf, postgres_engine, register  # noqa: F401
from test_account_email_verification import confirm, registered
from test_account_login import login, verified
from test_account_refresh import refresh

pytestmark = pytest.mark.postgres
NEW_PASSWORD = 'A completely different secure passphrase!'


def request_recovery(client, email='person@example.org', headers=None):
    return client.post('/api/v1/auth/recovery/request', json=dict(email=email), headers=headers or csrf(client))


def reset(client, token, password=NEW_PASSWORD, headers=None):
    return client.post('/api/v1/auth/recovery/confirm', json=dict(token=token, password=password), headers=headers or csrf(client))


def recoverable(client, app):
    verified(client, app)
    assert request_recovery(client).status_code == 202
    return app.state.test_mailer.recovery_deliveries[-1][1]


def test_register_verify_login_recover_new_password_and_old_sessions_revoked(auth_client, auth_app):
    assert confirm(auth_client, registered(auth_client, auth_app)).status_code == 204
    assert login(auth_client).status_code == 200
    headers = csrf(auth_client); old_cookies = Cookies(auth_client.cookies)
    assert request_recovery(auth_client, headers=headers).status_code == 202
    token = auth_app.state.test_mailer.recovery_deliveries[-1][1]
    with Session(auth_app.state.engine) as db:
        user_id = db.scalar(select(AccountUser.id))
        action = db.get(AccountActionToken, credential_digest('reset_password', token))
        assert action.expires_at-action.created_at == timedelta(minutes=30)
    with TestClient(auth_app) as anonymous:
        response = reset(anonymous, token)
        assert response.status_code == 204 and response.content == b'' and 'set-cookie' not in response.headers
        assert anonymous.get('/api/v1/auth/session').status_code == 401
        assert reset(anonymous, token).status_code == 400
    assert auth_client.get('/api/v1/auth/session').status_code == 401
    with TestClient(auth_app) as stale:
        stale.cookies.update(old_cookies)
        assert refresh(stale, headers).status_code == 401
    assert login(auth_client).status_code == 401
    assert login(auth_client, password=NEW_PASSWORD).status_code == 200
    assert auth_client.get('/api/v1/auth/session').json()['account']['id'] == user_id
    with Session(auth_app.state.engine) as db:
        assert verify_password(NEW_PASSWORD, db.scalar(select(AccountUser.password_hash))).valid
        assert all(t.used_at is not None for t in db.scalars(select(AccountActionToken)))


def test_reset_revokes_all_target_sessions_but_not_other_account_or_guest(auth_client, auth_app):
    from test_api import create
    auth_client.post('/api/v1/session', headers=HEADERS); watch = create(auth_client)
    verified(auth_client, auth_app); assert login(auth_client).status_code == 200
    with TestClient(auth_app) as same_user, TestClient(auth_app) as other_user:
        assert login(same_user).status_code == 200
        verified(other_user, auth_app, 'second@example.org'); assert login(other_user, email='second@example.org').status_code == 200
        before_other = dict(other_user.cookies)
        assert request_recovery(auth_client).status_code == 202
        token = auth_app.state.test_mailer.recovery_deliveries[-1][1]
        assert reset(other_user, token).status_code == 204
        assert dict(other_user.cookies) == before_other
        assert other_user.get('/api/v1/auth/session').json()['account']['email'] == 'second@example.org'
        assert same_user.get('/api/v1/auth/session').status_code == 401
    assert auth_client.get('/api/v1/auth/session').status_code == 401
    assert auth_client.get(f"/api/v1/watches/{watch['id']}").status_code == 200
    with Session(auth_app.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(AccountSession)) == 3


@pytest.mark.parametrize('kind', ['missing', 'unverified', 'disabled'])
def test_recovery_ineligible_addresses_are_uniform_and_deliver_generic_notice(auth_client, auth_app, kind):
    if kind != 'missing':
        registered(auth_client, auth_app)
        if kind == 'disabled':
            with Session(auth_app.state.engine) as db:
                user = db.scalar(select(AccountUser)); user.email_verified_at = datetime.now(timezone.utc)
                user.status = 'disabled'; db.commit()
    response = request_recovery(auth_client)
    assert response.status_code == 202
    assert response.json() == dict(message='Запрос принят. Если операция доступна для этого адреса, проверьте почту.')
    assert auth_app.state.test_mailer.recovery_deliveries[-1] == ('person@example.org', None)
    with Session(auth_app.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(AccountActionToken).where(AccountActionToken.purpose == 'reset_password')) == 0


@pytest.mark.parametrize('kind', ['forged', 'expired', 'used', 'wrong_purpose', 'deleted', 'disabled', 'unverified'])
def test_reset_invalid_tokens_are_uniform_and_do_not_change_password(auth_client, auth_app, kind):
    token = recoverable(auth_client, auth_app)
    with Session(auth_app.state.engine) as db:
        user = db.scalar(select(AccountUser)); original = user.password_hash
        action = db.get(AccountActionToken, credential_digest('reset_password', token)); now = datetime.now(timezone.utc)
        if kind == 'expired': action.created_at = now-timedelta(days=2); action.expires_at = now-timedelta(days=1)
        elif kind == 'used': action.used_at = now
        elif kind == 'wrong_purpose': action.purpose = 'verify_email'; action.token_hash = credential_digest('verify_email', token)
        elif kind == 'deleted': db.delete(user)
        elif kind == 'disabled': user.status = 'disabled'
        elif kind == 'unverified': user.email_verified_at = None
        db.commit()
    if kind == 'forged': token = new_token()
    response = reset(auth_client, token)
    assert response.status_code == 400 and response.json()['code'] == 'invalid_token'
    assert token not in response.text and NEW_PASSWORD not in response.text and 'set-cookie' not in response.headers
    with Session(auth_app.state.engine) as db:
        user = db.scalar(select(AccountUser))
        if user: assert user.password_hash == original


def test_recovery_resend_and_weak_password_do_not_reuse_old_token(auth_client, auth_app):
    old = recoverable(auth_client, auth_app)
    assert request_recovery(auth_client).status_code == 202
    current = auth_app.state.test_mailer.recovery_deliveries[-1][1]
    assert reset(auth_client, old).status_code == 400
    weak = reset(auth_client, current, password='short')
    assert weak.status_code == 422 and 'short' not in weak.text
    assert reset(auth_client, current).status_code == 204


def test_simultaneous_reset_consumes_token_once(auth_client, auth_app):
    token = recoverable(auth_client, auth_app); barrier = Barrier(2)
    def attempt(index):
        with TestClient(auth_app) as browser:
            headers = csrf(browser); barrier.wait(timeout=10)
            return reset(browser, token, password=NEW_PASSWORD+str(index), headers=headers).status_code
    with ThreadPoolExecutor(2) as pool: assert sorted(pool.map(attempt, range(2))) == [204, 400]
    with Session(auth_app.state.engine) as db:
        encoded = db.scalar(select(AccountUser.password_hash))
        assert sum(verify_password(NEW_PASSWORD+str(i), encoded).valid for i in range(2)) == 1


@pytest.mark.parametrize('winner', ['reset', 'refresh'])
def test_reset_refresh_serializations_never_restore_old_credentials(auth_client, auth_app, monkeypatch, winner):
    token = recoverable(auth_client, auth_app); assert login(auth_client).status_code == 200
    headers = csrf(auth_client); saved = Cookies(auth_client.cookies)
    reached, release = Event(), Event()
    module, name = (account_api, 'lock_family') if winner == 'reset' else (account_actions, '_lock_user')
    original = getattr(module, name)
    def paused(*args):
        reached.set(); assert release.wait(10)
        return original(*args)
    monkeypatch.setattr(module, name, paused)
    def loser():
        with TestClient(auth_app) as browser:
            if winner == 'reset': browser.cookies.update(saved); return refresh(browser, headers).status_code
            return reset(browser, token).status_code
    with ThreadPoolExecutor(1) as pool:
        pending = pool.submit(loser); assert reached.wait(10)
        try:
            if winner == 'reset':
                with TestClient(auth_app) as browser: assert reset(browser, token).status_code == 204
            else: assert refresh(auth_client, headers).status_code == 200
        finally: release.set()
        assert pending.result(timeout=10) == (401 if winner == 'reset' else 204)
    assert auth_client.get('/api/v1/auth/session').status_code == 401
    with Session(auth_app.state.engine) as db:
        assert all(s.revoked_at is not None for s in db.scalars(select(AccountSession)))


def test_reset_commit_failure_rolls_back_hash_token_and_revocation(auth_client, auth_app, monkeypatch):
    from sqlalchemy.exc import SQLAlchemyError
    token = recoverable(auth_client, auth_app); assert login(auth_client).status_code == 200
    with Session(auth_app.state.engine) as db: original_hash = db.scalar(select(AccountUser.password_hash))
    original_commit = Session.commit
    def fail_reset(db):
        if any(isinstance(obj, AccountUser) and obj.password_hash != original_hash for obj in db.identity_map.values()):
            raise SQLAlchemyError('private reset database failure')
        return original_commit(db)
    with monkeypatch.context() as patch:
        patch.setattr(Session, 'commit', fail_reset)
        response = reset(auth_client, token)
        assert response.status_code == 503 and 'set-cookie' not in response.headers
    with Session(auth_app.state.engine) as db:
        assert db.scalar(select(AccountUser.password_hash)) == original_hash
        assert db.get(AccountActionToken, credential_digest('reset_password', token)).used_at is None
        assert db.scalar(select(AccountSession)).revoked_at is None
    assert reset(auth_client, token).status_code == 204


def test_recovery_provider_failure_is_generic_and_never_changes_password(auth_client, auth_app):
    verified(auth_client, auth_app)
    with Session(auth_app.state.engine) as db: original = db.scalar(select(AccountUser.password_hash))
    auth_app.state.test_mailer.fail = True
    first = request_recovery(auth_client); missing = request_recovery(auth_client, 'missing@example.org')
    assert first.status_code == missing.status_code == 503 and first.json() == missing.json()
    with Session(auth_app.state.engine) as db: assert db.scalar(select(AccountUser.password_hash)) == original
