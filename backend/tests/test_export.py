from sqlalchemy.orm import Session

from app.database import Snapshot
from app.main import utcnow
from test_api import create, start


def test_export_requires_session(client):
    assert client.get('/api/v1/export').status_code == 401


def test_export_includes_full_history_beyond_detail_limit(client, application):
    start(client)
    watch_id = create(client)['id']
    with Session(application.state.engine) as db:
        db.add_all([Snapshot(watch_id=watch_id, captured_at=utcnow(), rank=10, seats=5, excluded=0, no_consent=0) for _ in range(149)])
        db.commit()
    assert len(client.get(f'/api/v1/watches/{watch_id}').json()['history']) == 100
    response = client.get('/api/v1/export')
    assert response.status_code == 200
    assert 'attachment' in response.headers['content-disposition']
    assert response.headers['cache-control'] == 'no-store'
    data = response.json()
    assert set(data) == {'formatVersion', 'exportedAt', 'watches'}
    assert data['formatVersion'] == 'manual-export-v1'
    assert len(data['watches'][0]['history']) == 150
    assert data['watches'][0]['latest'] == data['watches'][0]['history'][0]
    assert 'ownerHash' not in data['watches'][0]


def test_export_does_not_include_another_session(client):
    start(client)
    first_id = create(client)['id']
    client.cookies.clear()
    start(client)
    second_id = create(client)['id']
    data = client.get('/api/v1/export').json()
    assert [watch['id'] for watch in data['watches']] == [second_id]
    assert second_id != first_id


def test_empty_export_is_valid(client):
    start(client)
    response = client.get('/api/v1/export')
    assert response.status_code == 200
    assert response.json()['watches'] == []
