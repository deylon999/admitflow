from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from threading import Barrier

import pytest
from fastapi.testclient import TestClient
from httpx import Cookies
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.account_api import ACCESS_COOKIE, CSRF_COOKIE, REFRESH_COOKIE
from app.accounts import AccountCsrfContext, AccountRefreshToken, AccountSession
from app.main import COOKIE
from account_support import HEADERS, auth_app, auth_client, csrf, postgres_engine  # noqa: F401
from test_account_refresh import refresh, start

pytestmark = pytest.mark.postgres


def logout(client, headers):
    return client.post('/api/v1/auth/logout', json={}, headers=headers)


def test_logout_revokes_family_deletes_exact_cookies_and_preserves_guest(auth_client, auth_app):
    from test_api import create
    assert auth_client.post('/api/v1/session', headers=HEADERS).status_code == 204
    guest = auth_client.cookies.get(COOKIE); watch = create(auth_client)
    headers = start(auth_client, auth_app); original = dict(auth_client.cookies)
    response = logout(auth_client, headers)
    assert response.status_code == 204 and response.content == b''
    deleted = response.headers.get_list('set-cookie')
    assert len(deleted) == 3 and all('Max-Age=0' in c and 'HttpOnly' in c and 'SameSite=lax' in c for c in deleted)
    assert any(REFRESH_COOKIE+'=' in c and 'Path=/api/v1/auth' in c for c in deleted)
    assert all('Domain=' not in c for c in deleted)
    assert all(name not in auth_client.cookies for name in (ACCESS_COOKIE, REFRESH_COOKIE, CSRF_COOKIE))
    assert auth_client.cookies.get(COOKIE) == guest
    assert auth_client.get(f"/api/v1/watches/{watch['id']}").status_code == 200
    with TestClient(auth_app) as old:
        old.cookies.update(original)
        assert old.get('/api/v1/auth/session').status_code == 401
        assert refresh(old, headers).status_code == 401
        # Replaying the same valid logout proof is idempotent despite revocation.
        assert logout(old, headers).status_code == 204
    with Session(auth_app.state.engine) as db:
        assert db.scalar(select(AccountSession)).revoked_at is not None
        assert all(token.consumed_at is not None for token in db.scalars(select(AccountRefreshToken)))
        context = db.scalar(select(AccountCsrfContext))
        assert context.expires_at <= datetime.now(timezone.utc)+timedelta(minutes=30)
    # After cookies are gone, obtain anonymous CSRF rather than bypassing the guard.
    assert logout(auth_client, HEADERS).status_code == 403
    assert logout(auth_client, csrf(auth_client)).status_code == 204


def test_logout_with_expired_access_uses_refresh_identity(auth_client, auth_app):
    headers = start(auth_client, auth_app)
    auth_client.cookies.delete(ACCESS_COOKIE, domain='testserver.local', path='/api/v1')
    assert logout(auth_client, headers).status_code == 204
    with Session(auth_app.state.engine) as db:
        assert db.scalar(select(AccountSession)).revoked_at is not None


def test_logout_without_refresh_uses_access_and_does_not_touch_other_session(auth_client, auth_app):
    from test_account_login import login
    headers = start(auth_client, auth_app)
    first = dict(auth_client.cookies)
    with TestClient(auth_app) as other:
        assert login(other).status_code == 200
        second_headers = csrf(other)
        auth_client.cookies.delete(REFRESH_COOKIE, domain='testserver.local', path='/api/v1/auth')
        assert logout(auth_client, headers).status_code == 204
        assert other.get('/api/v1/auth/session').status_code == 200
        assert refresh(other, second_headers).status_code == 200
    with TestClient(auth_app) as expired:
        expired.cookies.update(first)
        assert expired.get('/api/v1/auth/session').status_code == 401


def test_logout_cannot_revoke_another_accounts_family(auth_client, auth_app):
    from test_account_login import login, verified
    headers = start(auth_client, auth_app)
    with TestClient(auth_app) as other:
        verified(other, auth_app, 'other@example.org')
        assert login(other, email='other@example.org').status_code == 200
        # A's proof cannot authorize B's cookies.
        assert logout(other, headers).status_code == 403
        assert other.get('/api/v1/auth/session').status_code == 200
    assert auth_client.get('/api/v1/auth/session').status_code == 200


def test_unknown_credentials_only_cleared_with_fresh_anonymous_csrf(auth_client):
    headers = csrf(auth_client)
    auth_client.cookies.set(ACCESS_COOKIE, 'x'*43, domain='testserver.local', path='/api/v1')
    auth_client.cookies.set(REFRESH_COOKIE, 'y'*43, domain='testserver.local', path='/api/v1/auth')
    assert logout(auth_client, headers).status_code == 204
    assert not auth_client.cookies


def test_expired_family_and_expired_csrf_require_fresh_anonymous_proof(auth_client, auth_app):
    headers = start(auth_client, auth_app)
    with Session(auth_app.state.engine) as db:
        session = db.scalar(select(AccountSession)); now = datetime.now(timezone.utc)
        session.created_at = now-timedelta(days=10)
        session.idle_expires_at = now-timedelta(days=1)
        context = db.scalar(select(AccountCsrfContext))
        context.created_at = now-timedelta(days=2); context.expires_at = now-timedelta(days=1)
        db.commit()
    assert logout(auth_client, headers).status_code == 403
    assert logout(auth_client, csrf(auth_client)).status_code == 204
    with Session(auth_app.state.engine) as db:
        assert db.scalar(select(AccountSession)).revoked_at is not None


def test_simultaneous_refresh_logout_never_resurrects_family(auth_client, auth_app):
    headers = start(auth_client, auth_app); saved = Cookies(auth_client.cookies)
    barrier = Barrier(2)
    def attempt(operation):
        with TestClient(auth_app) as browser:
            browser.cookies.update(saved); barrier.wait(timeout=10)
            result = refresh(browser, headers) if operation == 'refresh' else logout(browser, headers)
            return operation, result.status_code, Cookies(browser.cookies)
    with ThreadPoolExecutor(2) as pool:
        outcomes = list(pool.map(attempt, ['refresh', 'logout']))
    assert next(status for op, status, _ in outcomes if op == 'logout') == 204
    assert next(status for op, status, _ in outcomes if op == 'refresh') in (200, 401)
    with Session(auth_app.state.engine) as db:
        assert db.scalar(select(AccountSession)).revoked_at is not None
        assert db.scalar(select(func.count()).select_from(AccountSession)) == 1
    for _, _, cookies in outcomes:
        with TestClient(auth_app) as stale:
            stale.cookies.update(cookies)
            assert stale.get('/api/v1/auth/session').status_code == 401


def test_failed_revocation_never_deletes_cookies_or_claims_success(auth_client, auth_app, monkeypatch):
    from sqlalchemy.exc import SQLAlchemyError
    headers = start(auth_client, auth_app); saved = dict(auth_client.cookies)
    original = Session.commit
    def fail_family_commit(db):
        if any(isinstance(obj, AccountSession) for obj in db.identity_map.values()):
            raise SQLAlchemyError('private database failure')
        return original(db)
    monkeypatch.setattr(Session, 'commit', fail_family_commit)
    result = logout(auth_client, headers)
    assert result.status_code == 503 and 'set-cookie' not in result.headers
    assert dict(auth_client.cookies) == saved and 'private database' not in result.text
    assert auth_client.get('/api/v1/auth/session').status_code == 200
    with Session(auth_app.state.engine) as db:
        assert db.scalar(select(AccountSession)).revoked_at is None
        assert db.scalar(select(AccountRefreshToken)).consumed_at is None
