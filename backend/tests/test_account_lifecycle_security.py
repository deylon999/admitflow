from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from httpx import Cookies
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.account_api import ACCESS_COOKIE, CSRF_COOKIE, REFRESH_COOKIE
from app.account_limits import Budget, consume_budgets
from app.account_security import credential_digest
from app.accounts import AccountCsrfContext, AccountRefreshToken, AccountSession, AccountUser
from app.config import Settings
from app.main import create_app
from account_support import HEADERS, KEY, PASSWORD, RecordingMailer, auth_app, auth_client, csrf, postgres_engine  # noqa: F401
from test_account_login import login, verified
from test_account_logout import logout
from test_account_refresh import refresh, start

pytestmark = pytest.mark.postgres


@pytest.mark.parametrize('operation', ['refresh', 'logout'])
@pytest.mark.parametrize('kind', ['missing', 'wrong', 'foreign', 'expired', 'origin', 'cross_site', 'write_header'])
def test_sensitive_writes_reject_csrf_and_origin_without_revocation(auth_client, auth_app, operation, kind):
    headers = start(auth_client, auth_app)
    if kind == 'missing': headers.pop('X-CSRF-Token')
    elif kind == 'wrong': headers['X-CSRF-Token'] = 'x'*43
    elif kind == 'foreign':
        with TestClient(auth_app) as stranger:
            headers = csrf(stranger)
            auth_client.cookies.set(CSRF_COOKIE, stranger.cookies.get(CSRF_COOKIE), domain='testserver.local', path='/api/v1')
    elif kind == 'expired':
        with Session(auth_app.state.engine) as db:
            ctx = db.scalar(select(AccountCsrfContext)); now = datetime.now(timezone.utc)
            ctx.created_at = now-timedelta(hours=2); ctx.expires_at = now-timedelta(hours=1); db.commit()
    elif kind == 'origin': headers['Origin'] = 'http://evil.example'
    elif kind == 'cross_site': headers['Sec-Fetch-Site'] = 'cross-site'
    else: headers.pop('X-Requested-With')
    response = auth_client.post('/api/v1/auth/'+operation, json={}, headers=headers)
    assert response.status_code == 403 and 'set-cookie' not in response.headers
    assert auth_client.get('/api/v1/auth/session').status_code == 200
    with Session(auth_app.state.engine) as db:
        assert db.scalar(select(AccountSession)).revoked_at is None
        assert db.scalar(select(func.count()).select_from(AccountRefreshToken)) == 1
        assert db.scalar(select(AccountRefreshToken)).consumed_at is None


def test_wrong_csrf_with_spent_refresh_cannot_force_revocation(auth_client, auth_app):
    headers = start(auth_client, auth_app); old_refresh = auth_client.cookies.get(REFRESH_COOKIE)
    assert refresh(auth_client, headers).status_code == 200
    auth_client.cookies.set(REFRESH_COOKIE, old_refresh, domain='testserver.local', path='/api/v1/auth')
    assert refresh(auth_client, headers | {'X-CSRF-Token':'x'*43}).status_code == 403
    assert auth_client.get('/api/v1/auth/session').status_code == 200


def test_spent_refresh_alone_cannot_bootstrap_bound_csrf(auth_client, auth_app):
    headers = start(auth_client, auth_app); old_refresh = auth_client.cookies.get(REFRESH_COOKIE)
    assert refresh(auth_client, headers).status_code == 200
    with TestClient(auth_app) as stale:
        stale.cookies.set(REFRESH_COOKIE, old_refresh, domain='testserver.local', path='/api/v1/auth')
        stale_headers = csrf(stale)
        with Session(auth_app.state.engine) as db:
            ctx = db.get(AccountCsrfContext, credential_digest('csrf_context', stale.cookies.get(CSRF_COOKIE)))
            assert ctx.session_id is None
        assert refresh(stale, stale_headers).status_code == 403
        assert stale.get('/api/v1/auth/session').json()['code'] == 'not_authenticated'
    assert auth_client.get('/api/v1/auth/session').status_code == 200


@pytest.mark.parametrize('operation', ['refresh', 'logout'])
def test_mixed_valid_account_cookies_never_mutate_either_family(auth_client, auth_app, operation):
    start(auth_client, auth_app); saved = Cookies(auth_client.cookies)
    with TestClient(auth_app) as other:
        verified(other, auth_app, 'second@example.org'); assert login(other, email='second@example.org').status_code == 200
        headers = csrf(other)
        for name, path in [(REFRESH_COOKIE, '/api/v1/auth'), (CSRF_COOKIE, '/api/v1')]:
            auth_client.cookies.set(name, other.cookies.get(name), domain='testserver.local', path=path)
        assert auth_client.post('/api/v1/auth/'+operation, json={}, headers=headers).status_code == 403
        assert other.get('/api/v1/auth/session').status_code == 200
    auth_client.cookies.clear(); auth_client.cookies.update(saved)
    assert auth_client.get('/api/v1/auth/session').status_code == 200
    with Session(auth_app.state.engine) as db:
        assert all(s.revoked_at is None for s in db.scalars(select(AccountSession)))
        assert all(t.consumed_at is None for t in db.scalars(select(AccountRefreshToken)))


def test_failed_rotation_rolls_back_consumption_and_never_sets_cookies(auth_client, auth_app, monkeypatch):
    from sqlalchemy.exc import SQLAlchemyError
    headers = start(auth_client, auth_app); saved = dict(auth_client.cookies)
    original = Session.commit
    def fail_rotation(db):
        if any(isinstance(obj, AccountRefreshToken) for obj in db.new):
            raise SQLAlchemyError('private rotation error')
        return original(db)
    monkeypatch.setattr(Session, 'commit', fail_rotation)
    response = refresh(auth_client, headers)
    assert response.status_code == 503 and 'set-cookie' not in response.headers and 'private rotation' not in response.text
    assert dict(auth_client.cookies) == saved
    with Session(auth_app.state.engine) as db:
        assert db.scalar(select(AccountRefreshToken)).consumed_at is None
        assert db.scalar(select(func.count()).select_from(AccountRefreshToken)) == 1
    assert auth_client.get('/api/v1/auth/session').status_code == 200


def test_failed_replay_revocation_does_not_report_committed_incident(auth_client, auth_app, monkeypatch, caplog):
    from sqlalchemy.exc import SQLAlchemyError
    headers = start(auth_client, auth_app); saved = Cookies(auth_client.cookies)
    assert refresh(auth_client, headers).status_code == 200
    original = Session.commit
    def fail_revocation(db):
        if any(isinstance(obj, AccountSession) and obj.revoked_at is not None for obj in db.identity_map.values()):
            raise SQLAlchemyError('private revoke error')
        return original(db)
    with monkeypatch.context() as patch:
        patch.setattr(Session, 'commit', fail_revocation)
        with TestClient(auth_app) as replay:
            replay.cookies.update(saved)
            response = refresh(replay, headers)
            assert response.status_code == 503 and 'set-cookie' not in response.headers
    assert 'reuse revoked' not in caplog.text
    assert auth_client.get('/api/v1/auth/session').status_code == 200
    with Session(auth_app.state.engine) as db:
        assert db.scalar(select(AccountSession)).revoked_at is None


@pytest.mark.parametrize('scope', ['peer', 'session'])
def test_refresh_budgets_are_durable_and_forwarded_headers_cannot_bypass(auth_client, auth_app, monkeypatch, scope):
    from app import account_api
    fixed = datetime.now(timezone.utc)
    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None): return fixed
    monkeypatch.setattr(account_api, 'datetime', FixedDateTime)
    headers = start(auth_client, auth_app)
    if scope == 'peer': rule = Budget('refresh-peer', ('peer', '192.0.2.1'), 120, 900)
    else:
        with Session(auth_app.state.engine) as db: session_id = db.scalar(select(AccountSession.id))
        rule = Budget('refresh-session', ('session', session_id), 60, 900)
    for _ in range(rule.limit): consume_budgets(auth_app.state.engine, KEY, [rule], now=fixed)
    with TestClient(auth_app, client=('192.0.2.1' if scope == 'peer' else '192.0.2.2', 6000)) as restarted:
        restarted.cookies.update(auth_client.cookies)
        response = refresh(restarted, headers | {'X-Forwarded-For':'203.0.113.9', 'X-Real-IP':'203.0.113.9'})
        assert response.status_code == 429 and 1 <= int(response.headers['retry-after']) <= 900
    with Session(auth_app.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(AccountRefreshToken)) == 1
        assert db.scalar(select(AccountRefreshToken)).consumed_at is None


def test_revocation_survives_new_application_engine(auth_client, auth_app, postgres_engine):
    headers = start(auth_client, auth_app); saved = Cookies(auth_client.cookies)
    assert logout(auth_client, headers).status_code == 204
    app = create_app(Settings(database_url=postgres_engine.url.render_as_string(hide_password=False),
                             auto_create_schema=False, auth_enabled=True, auth_rate_key=KEY))
    with TestClient(app) as restarted:
        restarted.cookies.update(saved)
        assert restarted.get('/api/v1/auth/session').status_code == 401
        assert refresh(restarted, headers).status_code == 401
        assert logout(restarted, headers).status_code == 204


def test_production_rotation_and_deletion_keep_cookie_security_contract(postgres_engine):
    config = Settings(database_url=postgres_engine.url.render_as_string(hide_password=False), environment='production',
                      secure_cookie=True, auto_create_schema=False, allowed_hosts=('example.org',),
                      public_origin='https://example.org', auth_enabled=True, auth_rate_key=KEY)
    app = create_app(config, registration_mailer=RecordingMailer())
    headers = {'X-Requested-With':'abiturient', 'Origin':'https://example.org'}
    with TestClient(app, base_url='https://example.org') as browser:
        headers['X-CSRF-Token'] = browser.get('/api/v1/auth/csrf', headers=headers).json()['csrfToken']
        assert browser.post('/api/v1/auth/register', headers=headers, json=dict(email='person@example.org',password=PASSWORD)).status_code == 202
        with Session(postgres_engine) as db:
            db.scalar(select(AccountUser)).email_verified_at = datetime.now(timezone.utc); db.commit()
        assert browser.post('/api/v1/auth/login', headers=headers, json=dict(email='person@example.org',password=PASSWORD)).status_code == 200
        headers['X-CSRF-Token'] = browser.get('/api/v1/auth/csrf', headers=headers).json()['csrfToken']
        for operation in ('refresh', 'logout'):
            response = browser.post('/api/v1/auth/'+operation, json={}, headers=headers)
            assert response.status_code == (200 if operation == 'refresh' else 204)
            cookies = response.headers.get_list('set-cookie')
            assert len(cookies) == 3
            assert all('Secure' in c and 'HttpOnly' in c and 'SameSite=lax' in c and 'Domain=' not in c for c in cookies)
            assert any(REFRESH_COOKIE+'=' in c and 'Path=/api/v1/auth' in c for c in cookies)
            if operation == 'logout': assert all('Max-Age=0' in c for c in cookies)


def test_csrf_bootstrap_waiting_on_logout_cannot_rebind_revoked_family(auth_client, auth_app, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event, Lock
    from app import account_api
    headers = start(auth_client, auth_app); saved = Cookies(auth_client.cookies)
    reached, released, mutex = Event(), Event(), Lock()
    first = True
    original = account_api.lock_family
    def paused_first_lock(db, ids):
        nonlocal first
        with mutex:
            pause = first; first = False
        if pause:
            reached.set(); assert released.wait(10)
        return original(db, ids)
    monkeypatch.setattr(account_api, 'lock_family', paused_first_lock)
    def bootstrap():
        with TestClient(auth_app) as browser:
            browser.cookies.update(saved)
            result = browser.get('/api/v1/auth/csrf', headers=HEADERS)
            return result.status_code, browser.cookies.get(CSRF_COOKIE)
    with ThreadPoolExecutor(1) as pool:
        pending = pool.submit(bootstrap)
        assert reached.wait(10)
        try: assert logout(auth_client, headers).status_code == 204
        finally: released.set()
        status, token = pending.result(timeout=10)
    assert status == 200
    with Session(auth_app.state.engine) as db:
        context = db.get(AccountCsrfContext, credential_digest('csrf_context', token))
        assert context.session_id is None
        assert db.scalar(select(AccountSession)).revoked_at is not None


def test_refresh_extends_idle_within_unchanged_absolute_deadline(auth_client, auth_app, monkeypatch):
    from app import account_api
    headers = start(auth_client, auth_app)
    with Session(auth_app.state.engine) as db:
        session = db.scalar(select(AccountSession))
        original_idle, absolute = session.idle_expires_at, session.expires_at
    later = datetime.now(timezone.utc)+timedelta(days=2)
    class LaterDateTime(datetime):
        @classmethod
        def now(cls, tz=None): return later
    monkeypatch.setattr(account_api, 'datetime', LaterDateTime)
    assert auth_client.get('/api/v1/auth/session').json()['code'] == 'access_expired'
    assert refresh(auth_client, headers).status_code == 200
    with Session(auth_app.state.engine) as db:
        session = db.scalar(select(AccountSession))
        assert session.expires_at == absolute
        assert session.idle_expires_at == later+timedelta(days=7) > original_idle
        assert session.access_expires_at == later+timedelta(minutes=15)
        current = db.get(AccountRefreshToken, credential_digest('refresh', auth_client.cookies.get(REFRESH_COOKIE)))
        assert current.expires_at == session.idle_expires_at
