from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.admissions import Assessment, CandidateEntry, SourceSnapshot, Subscription
from app.database import OperationRecord
from test_api import HEADERS, start
from test_source_lookup import lookup_context
from test_subscriptions import confirm


def test_archive_delete_is_private_cascading_and_tombstones_replays(lookup_context):
    client, app = lookup_context; start(client)
    body = confirm(client)
    saved = client.post('/api/v1/subscriptions', json=body, headers=HEADERS).json()
    path = f"/api/v1/subscriptions/{saved['id']}"
    with TestClient(app) as other:
        start(other)
        assert other.delete(path, headers=HEADERS).status_code == 404
    assert client.delete(path).status_code == 403
    assert client.delete(path, headers=HEADERS).status_code == 204
    assert client.delete(path, headers=HEADERS).status_code == 404
    assert client.post('/api/v1/subscriptions', json=body, headers=HEADERS).status_code == 410
    assert client.get('/api/v1/direction-budget').json()['total'] == 0
    with Session(app.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(Assessment)) == 0
        assert db.scalar(select(func.count()).select_from(Subscription)) == 0
        tombstone = db.scalar(select(OperationRecord))
        assert tombstone.response_status == 410 and tombstone.response is None
        assert db.scalar(select(func.count()).select_from(CandidateEntry)) == 573
        assert db.scalar(select(func.count()).select_from(SourceSnapshot)) == 1


def test_delete_racing_with_success_replay_cannot_resurrect(lookup_context):
    client, app = lookup_context; start(client); body = confirm(client)
    saved = client.post('/api/v1/subscriptions', json=body, headers=HEADERS).json()
    def action(index):
        if index == 0: return client.delete(f"/api/v1/subscriptions/{saved['id']}", headers=HEADERS).status_code
        return client.post('/api/v1/subscriptions', json=body, headers=HEADERS).status_code
    with ThreadPoolExecutor(max_workers=4) as pool: results = list(pool.map(action, range(8)))
    assert results[0] == 204 and set(results[1:]) <= {201, 410}
    assert client.get('/api/v1/subscriptions').json() == []
