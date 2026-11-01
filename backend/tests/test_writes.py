from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import OperationRecord, Snapshot, Watch
from app.main import utcnow
from test_api import HEADERS, VALUES, WATCH, create, start


def headers(key):
    return {**HEADERS, 'Idempotency-Key': key}


def test_create_retry_returns_original_response_without_duplicates(client):
    start(client)
    first = client.post('/api/v1/watches', json=WATCH, headers=headers('same-create-key'))
    retry = client.post('/api/v1/watches', json=WATCH, headers=headers('same-create-key'))
    assert first.status_code == retry.status_code == 201
    assert first.json() == retry.json()
    assert len(client.get('/api/v1/watches').json()) == 1
    conflict = client.post('/api/v1/watches', json={**WATCH, 'title': 'Different'}, headers=headers('same-create-key'))
    assert conflict.status_code == 409


def test_snapshot_retry_does_not_extend_history_twice(client):
    start(client)
    watch_id = create(client)['id']
    path = f'/api/v1/watches/{watch_id}/snapshots'
    first = client.post(path, json=VALUES, headers=headers('same-snapshot-key'))
    retry = client.post(path, json=VALUES, headers=headers('same-snapshot-key'))
    assert first.status_code == retry.status_code == 201
    assert first.json() == retry.json()
    assert len(client.get(f'/api/v1/watches/{watch_id}').json()['history']) == 2


def test_delete_erases_cached_payload_and_does_not_resurrect_watch(client, application):
    start(client)
    response = client.post('/api/v1/watches', json=WATCH, headers=headers('deleted-create-key'))
    watch_id = response.json()['id']
    assert client.delete(f'/api/v1/watches/{watch_id}', headers=HEADERS).status_code == 204
    assert client.post('/api/v1/watches', json=WATCH, headers=headers('deleted-create-key')).status_code == 410
    with Session(application.state.engine) as db:
        operation = db.scalar(select(OperationRecord))
        assert operation.response is None and operation.watch_id is None
        assert db.scalar(select(func.count()).select_from(Watch)) == 0
    assert client.delete('/api/v1/session', headers=HEADERS).status_code == 204
    with Session(application.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(OperationRecord)) == 0


def test_idempotency_keys_are_scoped_to_owner(client):
    start(client)
    first = client.post('/api/v1/watches', json=WATCH, headers=headers('shared-key-for-test')).json()
    client.cookies.clear()
    start(client)
    second = client.post('/api/v1/watches', json=WATCH, headers=headers('shared-key-for-test')).json()
    assert first['id'] != second['id']
    assert len(client.get('/api/v1/watches').json()) == 1


def test_invalid_key_does_not_create_data(client):
    start(client)
    assert client.post('/api/v1/watches', json=WATCH, headers=headers('bad')).status_code == 400
    assert client.get('/api/v1/watches').json() == []


def test_concurrent_retries_create_one_watch(client):
    start(client)
    def send(_):
        return client.post('/api/v1/watches', json=WATCH, headers=headers('concurrent-retry-key'))
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(send, range(12)))
    assert all(item.status_code == 201 for item in results)
    assert len({item.json()['id'] for item in results}) == 1
    assert len(client.get('/api/v1/watches').json()) == 1


def test_concurrent_creation_cannot_exceed_watch_limit(client, application):
    start(client)
    def send(index):
        return client.post('/api/v1/watches', json=WATCH, headers=headers(f'parallel-create-{index}')).status_code
    with ThreadPoolExecutor(max_workers=6) as pool:
        statuses = list(pool.map(send, range(30)))
    assert statuses.count(201) == 20 and statuses.count(409) == 10
    with Session(application.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(Watch)) == 20


def test_concurrent_snapshots_cannot_exceed_history_limit(client, application):
    start(client)
    watch_id = create(client)['id']
    with Session(application.state.engine) as db:
        db.add_all([Snapshot(watch_id=watch_id, captured_at=utcnow(), rank=10, seats=5, excluded=0, no_consent=0) for _ in range(498)])
        db.commit()
    def send(index):
        return client.post(f'/api/v1/watches/{watch_id}/snapshots', json=VALUES, headers=headers(f'parallel-snapshot-{index}')).status_code
    with ThreadPoolExecutor(max_workers=3) as pool:
        statuses = list(pool.map(send, range(3)))
    assert statuses.count(201) == 1 and statuses.count(409) == 2
    with Session(application.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(Snapshot).where(Snapshot.watch_id == watch_id)) == 500
