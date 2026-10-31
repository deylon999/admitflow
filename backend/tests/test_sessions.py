from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import BrowserSession, Snapshot, Watch
from app.main import COOKIE, token_hash, utcnow
from app.maintenance import cleanup_expired_sessions
from test_api import HEADERS, create, start


def test_session_expiry_and_cookie_contract(client):
    response = client.post('/api/v1/session', headers=HEADERS)
    cookie = response.headers['set-cookie']
    assert 'HttpOnly' in cookie and 'SameSite=lax' in cookie
    assert 'Path=/api' in cookie and 'Max-Age=2592000' in cookie
    response = client.get('/api/v1/session')
    assert response.status_code == 200
    assert response.json()['expiresAt'].endswith('Z')


def test_expired_token_does_not_silently_create_another_session(client, application):
    start(client)
    original = client.cookies.get(COOKIE)
    with Session(application.state.engine) as db:
        db.get(BrowserSession, token_hash(original)).expires_at = utcnow() - timedelta(seconds=1)
        db.commit()
    assert client.post('/api/v1/session', headers=HEADERS).status_code == 401
    assert client.cookies.get(COOKIE) == original
    assert client.get('/api/v1/session').status_code == 401
    with Session(application.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(BrowserSession)) == 1


def test_explicit_reset_deletes_owned_data_and_allows_fresh_session(client, application):
    start(client)
    original = client.cookies.get(COOKIE)
    create(client)
    assert client.delete('/api/v1/session', headers=HEADERS).status_code == 204
    assert client.cookies.get(COOKIE) is None
    with Session(application.state.engine) as db:
        for model in (BrowserSession, Watch, Snapshot):
            assert db.scalar(select(func.count()).select_from(model)) == 0
    assert client.delete('/api/v1/session', headers=HEADERS).status_code == 204
    start(client)
    assert client.cookies.get(COOKIE) != original
    assert client.get('/api/v1/watches').json() == []


def test_session_delete_requires_write_header(client):
    start(client)
    assert client.delete('/api/v1/session').status_code == 403
    assert client.get('/api/v1/session').status_code == 200


def test_cleanup_removes_only_expired_sessions_and_cascades(client, application):
    start(client)
    active = token_hash(client.cookies.get(COOKIE))
    create(client)
    client.cookies.clear()
    start(client)
    create(client)
    expired = token_hash(client.cookies.get(COOKIE))
    now = utcnow()
    with Session(application.state.engine) as db:
        db.get(BrowserSession, expired).expires_at = now
        db.commit()
    assert cleanup_expired_sessions(application.state.engine, now=now) == 1
    assert cleanup_expired_sessions(application.state.engine, now=now) == 0
    with Session(application.state.engine) as db:
        assert db.get(BrowserSession, active) is not None
        assert db.get(BrowserSession, expired) is None
        assert db.scalar(select(func.count()).select_from(Watch)) == 1
        assert db.scalar(select(func.count()).select_from(Snapshot)) == 1
