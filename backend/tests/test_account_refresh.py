from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from threading import Barrier

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.account_api import ACCESS_COOKIE, CSRF_COOKIE, REFRESH_COOKIE
from app.account_security import credential_digest
from app.accounts import AccountCsrfContext, AccountRefreshToken, AccountSession, AccountUser
from app.database import BrowserSession
from account_support import HEADERS, auth_app, auth_client, csrf, postgres_engine  # noqa: F401
from test_account_login import login, verified

pytestmark = pytest.mark.postgres


def start(client, app):
    verified(client, app)
    assert login(client).status_code == 200
    return csrf(client)


def refresh(client, headers):
    return client.post('/api/v1/auth/refresh', json={}, headers=headers)


def test_rotation_replaces_credentials_and_keeps_csrf_and_identity(auth_client, auth_app):
    headers = start(auth_client, auth_app)
    before = dict(auth_client.cookies)
    original = auth_client.get('/api/v1/auth/session').json()
    result = refresh(auth_client, headers)
    assert result.status_code == 200
    assert result.json()['account'] == original['account']
    assert result.json()['absoluteExpiresAt'] == original['absoluteExpiresAt']
    assert auth_client.cookies.get(ACCESS_COOKIE) != before[ACCESS_COOKIE]
    assert auth_client.cookies.get(REFRESH_COOKIE) != before[REFRESH_COOKIE]
    assert auth_client.cookies.get(CSRF_COOKIE) == before[CSRF_COOKIE]
    with Session(auth_app.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(AccountUser)) == 1
        assert db.scalar(select(func.count()).select_from(AccountSession)) == 1
        assert db.scalar(select(func.count()).select_from(BrowserSession)) == 0
        old = db.get(AccountRefreshToken, credential_digest('refresh', before[REFRESH_COOKIE]))
        assert old.consumed_at is not None
        assert len(db.scalars(select(AccountRefreshToken)).all()) == 2
    with TestClient(auth_app) as stale_access:
        stale_access.cookies.set(ACCESS_COOKIE, before[ACCESS_COOKIE])
        assert stale_access.get('/api/v1/auth/session').status_code == 401
    for secret in before.values(): assert secret not in result.text


def test_access_expiry_and_missing_cookie_restore_through_refresh(auth_client, auth_app):
    headers = start(auth_client, auth_app)
    with Session(auth_app.state.engine) as db:
        session = db.scalar(select(AccountSession))
        session.created_at = datetime.now(timezone.utc)-timedelta(hours=1)
        session.access_expires_at = datetime.now(timezone.utc)-timedelta(seconds=1); db.commit()
    assert auth_client.get('/api/v1/auth/session').json()['code'] == 'access_expired'
    auth_client.cookies.delete(ACCESS_COOKIE, domain='testserver.local', path='/api/v1')
    assert auth_client.get('/api/v1/auth/session').json()['code'] == 'access_expired'
    # A lost/expired CSRF cookie can be re-bootstrapped only with current refresh.
    auth_client.cookies.delete(CSRF_COOKIE, domain='testserver.local', path='/api/v1')
    headers = csrf(auth_client)
    with Session(auth_app.state.engine) as db:
        digest = credential_digest('csrf_context', auth_client.cookies.get(CSRF_COOKIE))
        assert db.get(AccountCsrfContext, digest).session_id is not None
    assert refresh(auth_client, headers).status_code == 200
    assert auth_client.get('/api/v1/auth/session').status_code == 200


def test_replay_commits_family_revocation_and_logs_no_secrets(auth_client, auth_app, caplog):
    headers = start(auth_client, auth_app); saved = dict(auth_client.cookies)
    assert refresh(auth_client, headers).status_code == 200
    current = dict(auth_client.cookies)
    with TestClient(auth_app) as replay:
        replay.cookies.update(saved)
        assert refresh(replay, headers).status_code == 401
    assert auth_client.get('/api/v1/auth/session').status_code == 401
    assert refresh(auth_client, headers).status_code == 401
    with Session(auth_app.state.engine) as db:
        assert db.scalar(select(AccountSession)).revoked_at is not None
    assert 'reuse revoked' in caplog.text
    for token in [*saved.values(), *current.values(), headers['X-CSRF-Token']]: assert token not in caplog.text


def test_simultaneous_refresh_can_rotate_only_once_then_revokes(auth_client, auth_app):
    headers = start(auth_client, auth_app); saved = dict(auth_client.cookies)
    barrier = Barrier(2)
    def attempt(_):
        with TestClient(auth_app) as browser:
            browser.cookies.update(saved); barrier.wait(timeout=10)
            return refresh(browser, headers).status_code
    with ThreadPoolExecutor(2) as pool: assert sorted(pool.map(attempt, range(2))) == [200, 401]
    with Session(auth_app.state.engine) as db:
        assert db.scalar(select(AccountSession)).revoked_at is not None
        assert db.scalar(select(func.count()).select_from(AccountRefreshToken)) == 2


@pytest.mark.parametrize('kind', ['refresh_expired', 'idle_expired', 'absolute_expired', 'revoked', 'disabled', 'unverified', 'forged', 'guest'])
def test_terminal_refresh_credentials_never_reactivate(auth_client, auth_app, kind):
    headers = start(auth_client, auth_app)
    with Session(auth_app.state.engine) as db:
        session = db.scalar(select(AccountSession)); token = db.scalar(select(AccountRefreshToken))
        user = db.scalar(select(AccountUser)); now = datetime.now(timezone.utc)
        if kind == 'refresh_expired': token.created_at = now-timedelta(days=2); token.expires_at = now-timedelta(days=1)
        elif kind == 'idle_expired': session.created_at = now-timedelta(days=2); session.idle_expires_at = now-timedelta(days=1)
        elif kind == 'absolute_expired':
            session.created_at = now-timedelta(days=40); session.access_expires_at = now-timedelta(days=4)
            session.idle_expires_at = now-timedelta(days=3); session.expires_at = now-timedelta(days=2)
        elif kind == 'revoked': session.revoked_at = now
        elif kind == 'disabled': user.status = 'disabled'
        elif kind == 'unverified': user.email_verified_at = None
        db.commit()
    if kind in ('forged', 'guest'):
        if kind == 'guest':
            auth_client.post('/api/v1/session', headers=HEADERS); fake = auth_client.cookies.get('abiturient_session')
        else: fake = 'x'*43
        auth_client.cookies.set(REFRESH_COOKIE, fake, domain='testserver.local', path='/api/v1/auth')
    result = refresh(auth_client, headers)
    assert result.status_code == 401
    assert 'set-cookie' not in result.headers
    with Session(auth_app.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(AccountRefreshToken)) == 1


def test_absolute_deadline_caps_access_idle_refresh_and_csrf(auth_client, auth_app):
    headers = start(auth_client, auth_app)
    with Session(auth_app.state.engine) as db:
        session = db.scalar(select(AccountSession)); now = datetime.now(timezone.utc)
        session.created_at = now-timedelta(days=29)
        session.expires_at = now+timedelta(seconds=40)
        session.access_expires_at = session.idle_expires_at = session.expires_at
        db.scalar(select(AccountRefreshToken)).expires_at = session.expires_at
        db.commit()
    assert refresh(auth_client, headers).status_code == 200
    with Session(auth_app.state.engine) as db:
        session = db.scalar(select(AccountSession))
        current = db.get(AccountRefreshToken, credential_digest('refresh', auth_client.cookies.get(REFRESH_COOKIE)))
        assert session.access_expires_at == session.idle_expires_at == current.expires_at == session.expires_at
        assert db.scalar(select(AccountCsrfContext)).expires_at == session.expires_at
