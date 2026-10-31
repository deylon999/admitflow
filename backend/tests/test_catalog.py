from sqlalchemy.orm import Session

from app.admissions import University
from app.catalog import seed_catalog


def test_catalog_exposes_audited_manual_coverage_without_session(client):
    response = client.get('/api/v1/universities')
    assert response.status_code == 200
    catalog = response.json()
    assert catalog['total'] == 2
    assert all(item['coverage'] == 'manual' for item in catalog['items'])
    assert all(item['provenanceUrl'].startswith('https://') for item in catalog['items'])
    assert all(item['verifiedAt'].startswith('2026-11-01') for item in catalog['items'])


def test_catalog_search_handles_russian_case_and_whitespace(client):
    catalog = client.get('/api/v1/universities', params={'q': '  ЧЕРНЫШЕВСКОГО  '}).json()
    assert catalog['total'] == 1
    assert catalog['items'][0]['id'] == 'sgu-saratov'
    assert client.get('/api/v1/universities', params={'q': 'not-a-university'}).json() == {'items': [], 'total': 0}


def test_search_treats_sql_wildcards_as_literal_text(client):
    assert client.get('/api/v1/universities', params={'q': '%'}).json()['total'] == 0
    assert client.get('/api/v1/universities', params={'q': 'a' * 121}).status_code == 422


def test_seeding_is_idempotent_and_does_not_overwrite_edits(client, application):
    engine = application.state.engine
    with Session(engine) as db:
        db.get(University, 'sgu-saratov').name = 'Edited display name'
        db.commit()
    seed_catalog(engine)
    seed_catalog(engine)
    catalog = client.get('/api/v1/universities').json()
    assert catalog['total'] == 2
    assert next(item for item in catalog['items'] if item['id'] == 'sgu-saratov')['name'] == 'Edited display name'
