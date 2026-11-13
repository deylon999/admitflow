from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.account_api import ACCESS_COOKIE, CSRF_COOKIE
from app.account_security import credential_digest
from app.accounts import AccountCsrfContext, AccountRefreshToken, AccountSession, AccountUser
from app.database import BrowserSession
from app.main import COOKIE
from account_support import HEADERS, PASSWORD, auth_app, auth_client, csrf, postgres_engine, register  # noqa: F401

pytestmark = pytest.mark.postgres


def verified(client, app, email='person@example.org'):
    assert register(client, email=email).status_code == 202
    with Session(app.state.engine) as db:
        user = db.scalar(select(AccountUser).where(AccountUser.email == email))
        user.email_verified_at = datetime.now(timezone.utc); db.commit()
        return user.id


def login(client, email='person@example.org', password=PASSWORD, headers=None):
    return client.post('/api/v1/auth/login', json=dict(email=email, password=password),
                       headers=headers if headers is not None else csrf(client))


def test_login_real_credentials_new_session_cookie_and_reload(auth_client, auth_app):
    user_id = verified(auth_client, auth_app)
    assert auth_client.post('/api/v1/session', headers=HEADERS).status_code == 204
    guest = auth_client.cookies.get(COOKIE)
    previous_context = auth_client.cookies.get(CSRF_COOKIE)
    response = login(auth_client)
    assert response.status_code == 200
    assert set(response.json()) == {'account', 'accessExpiresAt', 'absoluteExpiresAt'}
    assert response.json()['account'] == dict(id=user_id, email='person@example.org', emailVerified=True)
    cookies = response.headers.get_list('set-cookie')
    assert all('HttpOnly' in c and 'SameSite=lax' in c and 'Path=/api/v1' in c and 'Domain=' not in c for c in cookies)
    assert auth_client.cookies.get(COOKIE) == guest
    assert auth_client.cookies.get(CSRF_COOKIE) != previous_context
    access = auth_client.cookies.get(ACCESS_COOKIE)
    assert access != guest and access not in response.text and PASSWORD not in response.text
    assert auth_client.get('/api/v1/auth/session').json() == response.json()
    with TestClient(auth_app) as reloaded:
        reloaded.cookies.update(auth_client.cookies)
        assert reloaded.get('/api/v1/auth/session').json() == response.json()
    with Session(auth_app.state.engine) as db:
        session = db.scalar(select(AccountSession))
        assert session.access_hash == credential_digest('access', access)
        assert session.user_id == user_id and session.access_expires_at-session.created_at == timedelta(minutes=15)
        assert db.scalar(select(func.count()).select_from(AccountRefreshToken)) == 0
        assert db.scalar(select(func.count()).select_from(BrowserSession)) == 1
        assert len(db.scalars(select(AccountCsrfContext)).all()) == 1


@pytest.mark.parametrize('kind', ['wrong_password', 'missing', 'unverified', 'disabled'])
def test_sensitive_login_denials_are_uniform(auth_client, auth_app, kind):
    if kind != 'missing':
        assert register(auth_client).status_code == 202
        with Session(auth_app.state.engine) as db:
            user = db.scalar(select(AccountUser))
            if kind != 'unverified': user.email_verified_at = datetime.now(timezone.utc)
            if kind == 'disabled': user.status = 'disabled'
            db.commit()
    response = login(auth_client, password=PASSWORD+'wrong' if kind == 'wrong_password' else PASSWORD)
    assert response.status_code == 401
    assert response.json() == dict(code='not_authenticated', detail='Не удалось подтвердить доступ к аккаунту.')
    assert ACCESS_COOKIE not in auth_client.cookies
    with Session(auth_app.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(AccountSession)) == 0


@pytest.mark.parametrize('kind', ['access_expired', 'idle_expired', 'revoked', 'disabled', 'unverified', 'forged', 'guest', 'deleted'])
def test_session_checks_real_server_state_every_time(auth_client, auth_app, kind):
    verified(auth_client, auth_app); assert login(auth_client).status_code == 200
    with Session(auth_app.state.engine) as db:
        session = db.scalar(select(AccountSession)); user = db.scalar(select(AccountUser))
        now = datetime.now(timezone.utc)
        if kind.endswith('_expired'):
            session.created_at = now-timedelta(days=10)
            if kind == 'access_expired': session.access_expires_at = now-timedelta(seconds=1)
            else: session.idle_expires_at = now-timedelta(seconds=1)
        elif kind == 'revoked': session.revoked_at = now
        elif kind == 'disabled': user.status = 'disabled'
        elif kind == 'unverified': user.email_verified_at = None
        elif kind == 'deleted': db.delete(user)
        db.commit()
    if kind in ('forged', 'guest'):
        auth_client.cookies.clear()
        if kind == 'guest':
            auth_client.post('/api/v1/session', headers=HEADERS)
            forged = auth_client.cookies.get(COOKIE)
        else: forged = 'x'*43
        auth_client.cookies.set(ACCESS_COOKIE, forged)
    response = auth_client.get('/api/v1/auth/session')
    assert response.status_code == 401 and response.json()['code'] == 'not_authenticated'


def test_password_attempts_persist_and_forwarded_addresses_do_not_bypass(auth_client, auth_app):
    headers = csrf(auth_client)
    responses = [login(auth_client, password='incorrect password', headers=headers | {'X-Forwarded-For':f'192.0.2.{i+10}', 'X-Real-IP':f'192.0.2.{i+10}'}) for i in range(11)]
    assert [r.status_code for r in responses] == [401]*10+[429]
    assert 1 <= int(responses[-1].headers['retry-after']) <= 900
    with TestClient(auth_app, client=('192.0.2.1', 6000)) as restarted:
        assert login(restarted).status_code == 429
    with TestClient(auth_app, client=('192.0.2.2', 6000)) as independent:
        assert login(independent).status_code == 401


def test_session_and_csrf_are_not_transferable_between_accounts(auth_client, auth_app):
    id1 = verified(auth_client, auth_app); assert login(auth_client).status_code == 200
    headers1 = csrf(auth_client)
    with TestClient(auth_app, client=('192.0.2.2', 5000)) as other:
        id2 = verified(other, auth_app, 'second@example.org')
        assert login(other, email='second@example.org').status_code == 200
        assert id1 != id2
        assert other.get('/api/v1/auth/session').json()['account']['id'] == id2
        other.cookies.set(CSRF_COOKIE, auth_client.cookies.get(CSRF_COOKIE), domain='testserver.local', path='/api/v1')
        assert login(other, email='second@example.org', headers=headers1).status_code == 403
    assert auth_client.get('/api/v1/auth/session').json()['account']['id'] == id1


def test_password_change_during_verification_cannot_issue_stale_session(auth_client, auth_app, monkeypatch):
    from app import account_api
    from app.account_security import hash_password
    verified(auth_client, auth_app)
    real = account_api.verify_password
    def changed_during_verify(value, encoded):
        checked = real(value, encoded)
        with Session(auth_app.state.engine) as db:
            user = db.scalar(select(AccountUser)); user.password_hash = hash_password(PASSWORD+' changed'); db.commit()
        return checked
    monkeypatch.setattr(account_api, 'verify_password', changed_during_verify)
    assert login(auth_client).status_code == 401
    with Session(auth_app.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(AccountSession)) == 0


def test_login_rehashes_verified_password_without_weak_test_parameters(auth_client, auth_app):
    from argon2 import PasswordHasher, extract_parameters
    verified(auth_client, auth_app)
    with Session(auth_app.state.engine) as db:
        user = db.scalar(select(AccountUser))
        user.password_hash = PasswordHasher(memory_cost=65536, time_cost=4, parallelism=4).hash(PASSWORD); db.commit()
    assert login(auth_client).status_code == 200
    with Session(auth_app.state.engine) as db:
        params = extract_parameters(db.scalar(select(AccountUser)).password_hash)
        assert (params.memory_cost, params.time_cost, params.parallelism) == (65536, 3, 4)


def test_concurrent_login_consumes_one_browser_context(auth_client, auth_app):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    verified(auth_client, auth_app); headers = csrf(auth_client)
    barrier = Barrier(2)
    def attempt(_):
        with TestClient(auth_app, client=('192.0.2.1', 5000)) as browser:
            browser.cookies.update(auth_client.cookies)
            barrier.wait(timeout=10)
            return login(browser, headers=headers).status_code
    with ThreadPoolExecutor(2) as pool:
        assert sorted(pool.map(attempt, range(2))) == [200, 403]
    with Session(auth_app.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(AccountSession)) == 1


def test_login_retains_guest_history_and_cannot_promote_guest_token(auth_client, auth_app):
    from test_api import create
    assert auth_client.post('/api/v1/session', headers=HEADERS).status_code == 204
    watch = create(auth_client); guest = auth_client.cookies.get(COOKIE)
    assert auth_client.get('/api/v1/auth/session').status_code == 401
    verified(auth_client, auth_app); assert login(auth_client).status_code == 200
    assert auth_client.cookies.get(COOKIE) == guest
    assert auth_client.get(f"/api/v1/watches/{watch['id']}").json()['id'] == watch['id']
    # Account identity does not acquire ownership of another guest's resources.
    with TestClient(auth_app, client=('192.0.2.2', 5000)) as other:
        other.cookies.set(ACCESS_COOKIE, auth_client.cookies.get(ACCESS_COOKIE))
        assert other.get('/api/v1/auth/session').status_code == 200
        assert other.get(f"/api/v1/watches/{watch['id']}").status_code == 401
        assert other.post('/api/v1/session', headers=HEADERS).status_code == 204
        assert other.get(f"/api/v1/watches/{watch['id']}").status_code == 404


def test_login_missing_csrf_and_revoked_context_rejected(auth_client, auth_app):
    verified(auth_client, auth_app)
    old_headers = csrf(auth_client)
    assert login(auth_client, headers=HEADERS).status_code == 403
    assert login(auth_client, headers=old_headers).status_code == 200
    assert login(auth_client, headers=old_headers).status_code == 403
