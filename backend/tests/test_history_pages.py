from sqlalchemy.orm import Session

from app.database import Snapshot
from app.main import utcnow
from test_api import create, start


def test_all_500_with_equal_timestamps_and_new_insert(client, application):
    start(client)
    watch = create(client)['id']
    stamp = utcnow()
    with Session(application.state.engine) as db:
        db.add_all([Snapshot(watch_id=watch, captured_at=stamp, rank=10, seats=5, excluded=0, no_consent=0) for _ in range(498)])
        db.commit()
    url = f'/api/v1/watches/{watch}/history'
    page = client.get(url).json()
    seen = [row['id'] for row in page['items']]
    inserted = client.post(f'/api/v1/watches/{watch}/snapshots', headers={'X-Requested-With':'abiturient'}, json={'rank':20,'seats':5,'excluded':0,'noConsent':0}).json()['id']
    while page['nextCursor']:
        response = client.get(url, params={'before':page['nextCursor']})
        assert response.status_code == 200
        page = response.json()
        seen.extend(row['id'] for row in page['items'])
    assert len(seen) == len(set(seen)) == 499
    assert inserted not in seen
    assert client.get(url).json()['items'][0]['id'] == inserted


def test_cursor_is_scoped_and_invalid_limits_rejected(client):
    start(client)
    first = create(client)
    second = create(client)
    url = f"/api/v1/watches/{first['id']}/history"
    assert client.get(url, params={'before':second['latest']['id']}).status_code == 400
    assert client.get(url, params={'limit':101}).status_code == 422
    assert client.get(url, params={'limit':0}).status_code == 422
    assert client.get(url).json()['nextCursor'] is None
    client.cookies.clear()
    start(client)
    assert client.get(url).status_code == 404
