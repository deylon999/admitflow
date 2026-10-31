from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import BrowserSession, Snapshot
from app.main import COOKIE, token_hash, utcnow

HEADERS = {'X-Requested-With': 'abiturient'}
VALUES = {'rank': 120, 'seats': 90, 'excluded': 30, 'noConsent': 16}
WATCH = {'university': 'Тестовый вуз', 'title': 'Информатика', 'sourceUrl': 'https://example.org/list', 'values': VALUES}


def start(client):
    assert client.post('/api/v1/session', headers=HEADERS).status_code == 204


def create(client):
    response = client.post('/api/v1/watches', json=WATCH, headers=HEADERS)
    assert response.status_code == 201
    return response.json()


def test_health_and_calculation_without_session(client):
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'
    assert response.headers['Cache-Control'] == 'no-store'
    result = client.post('/api/v1/calculate', json=VALUES)
    assert result.status_code == 200
    assert result.json()['place'] == 74


def test_manual_lifecycle(client, application):
    start(client)
    assert client.get('/api/v1/watches').json() == []
    watch = create(client)
    watch_id = watch['id']
    assert watch['latest']['sourceKind'] == 'manual'
    assert watch['latest']['modelVersion'] == 'manual-v1'
    assert watch['latest']['calculation']['place'] == 74
    assert len(client.get('/api/v1/watches').json()) == 1
    updated = client.post(f'/api/v1/watches/{watch_id}/snapshots', json={**VALUES, 'noConsent': 0}, headers=HEADERS)
    assert updated.status_code == 201
    detail = client.get(f'/api/v1/watches/{watch_id}').json()
    assert len(detail['history']) == 2
    assert detail['latest']['calculation']['place'] == 90
    assert detail['history'][1]['calculation']['place'] == 74
    assert client.delete(f'/api/v1/watches/{watch_id}', headers=HEADERS).status_code == 204
    assert client.get('/api/v1/watches').json() == []
    assert client.get(f'/api/v1/watches/{watch_id}').status_code == 404
    with Session(application.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(Snapshot)) == 0


def test_session_cookie_is_opaque_and_reused(client, application):
    start(client)
    token = client.cookies.get(COOKIE)
    assert token and len(token) >= 32
    start(client)
    assert client.cookies.get(COOKIE) == token
    with Session(application.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(BrowserSession)) == 1
        assert db.get(BrowserSession, token_hash(token)) is not None


def test_write_requires_custom_header(client):
    assert client.post('/api/v1/session').status_code == 403
    assert client.post('/api/v1/watches', json=WATCH).status_code == 403


def test_no_session_cannot_access_data(client):
    assert client.get('/api/v1/watches').status_code == 401
    assert client.post('/api/v1/watches', json=WATCH, headers=HEADERS).status_code == 401


def test_other_session_cannot_read_update_or_delete(client, application):
    start(client)
    watch_id = create(client)['id']
    with TestClient(application) as other:
        start(other)
        assert other.get('/api/v1/watches').json() == []
        assert other.get(f'/api/v1/watches/{watch_id}').status_code == 404
        assert other.post(f'/api/v1/watches/{watch_id}/snapshots', json=VALUES, headers=HEADERS).status_code == 404
        assert other.delete(f'/api/v1/watches/{watch_id}', headers=HEADERS).status_code == 404
    assert len(client.get('/api/v1/watches').json()) == 1


def test_expired_session_is_rejected(client, application):
    start(client)
    token = client.cookies.get(COOKIE)
    with Session(application.state.engine) as db:
        db.get(BrowserSession, token_hash(token)).expires_at = utcnow() - timedelta(seconds=1)
        db.commit()
    assert client.get('/api/v1/watches').status_code == 401


@pytest.mark.parametrize('patch', [
    {'university': ' '}, {'title': ''}, {'sourceUrl': 'file:///etc/passwd'},
    {'unexpected': True}, {'values': {**VALUES, 'excluded': 104}},
])
def test_invalid_watch_does_not_create_data(client, patch):
    start(client)
    assert client.post('/api/v1/watches', json={**WATCH, **patch}, headers=HEADERS).status_code == 422
    assert client.get('/api/v1/watches').json() == []


def test_invalid_update_preserves_history(client):
    start(client)
    watch_id = create(client)['id']
    assert client.post(f'/api/v1/watches/{watch_id}/snapshots', json={**VALUES, 'rank': 0}, headers=HEADERS).status_code == 422
    assert len(client.get(f'/api/v1/watches/{watch_id}').json()['history']) == 1


def test_sequential_watch_limit(client):
    start(client)
    for _ in range(20):
        create(client)
    assert client.post('/api/v1/watches', json=WATCH, headers=HEADERS).status_code == 409
    assert len(client.get('/api/v1/watches').json()) == 20
