import json
from pathlib import Path

from app.schemas import WatchRead
from test_api import HEADERS, start

FIXTURE = json.loads((Path(__file__).resolve().parents[2] / 'shared/manual-watch.json').read_text(encoding='utf-8'))


def test_shared_frontend_fixture_matches_real_api_contract(client):
    start(client)
    body = {key: FIXTURE[key] for key in ('university', 'title', 'sourceUrl')}
    body['values'] = FIXTURE['latest']['values']
    response = client.post('/api/v1/watches', json=body, headers=HEADERS)
    assert response.status_code == 201
    actual = response.json()
    for key in ('id', 'createdAt'):
        actual[key] = FIXTURE[key]
    for key in ('id', 'capturedAt'):
        actual['latest'][key] = FIXTURE['latest'][key]
    assert actual == FIXTURE
    assert WatchRead.model_validate(FIXTURE).model_dump(mode='json', by_alias=True) == FIXTURE


def test_urls_with_credentials_are_not_saved(client):
    start(client)
    body = {'university': 'Test', 'title': 'Test', 'sourceUrl': 'https://user:password@example.org/list', 'values': FIXTURE['latest']['values']}
    assert client.post('/api/v1/watches', json=body, headers=HEADERS).status_code == 422
    assert client.get('/api/v1/watches').json() == []
