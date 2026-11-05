from sqlalchemy.orm import Session

from app.admissions import University
from app.catalog import seed_catalog


def test_catalog_exposes_audited_manual_coverage_without_session(client):
    response = client.get('/api/v1/universities')
    assert response.status_code == 200
    catalog = response.json()
    assert catalog['total'] == 1257
    assert len(catalog['items']) == 50 and catalog['nextOffset'] == 50
    assert catalog['registryTotal'] == 1257 and catalog['registryEdition'] == 2025
    assert all(item['coverage'] == 'manual' for item in catalog['items'])
    assert all(item['provenanceUrl'].startswith('https://') for item in catalog['items'])
    assert all(item['verifiedAt'].startswith('2026-11-01') for item in catalog['items'] if item['catalogOrigin']=='operator')


def test_catalog_search_handles_russian_case_and_whitespace(client):
    catalog = client.get('/api/v1/universities', params={'q': '  ЧЕРНЫШЕВСКОГО  '}).json()
    assert 'sgu-saratov' in {item['id'] for item in catalog['items']}
    assert all('чернышевского' in (item['legalName'] or item['name']).casefold() for item in catalog['items'])
    missing = client.get('/api/v1/universities', params={'q': 'not-a-university'}).json()
    assert missing['items']==[] and missing['total']==0 and missing['nextOffset'] is None


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
    assert catalog['total'] == 1257
    assert next(item for item in catalog['items'] if item['id'] == 'sgu-saratov')['name'] == 'Edited display name'


def test_all_reference_records_are_reachable_by_bounded_pagination_without_guest(client):
    offset=0;items=[]
    while offset is not None:
        response=client.get('/api/v1/universities',params={'offset':offset})
        assert response.status_code==200 and 'set-cookie' not in response.headers
        data=response.json()
        assert 1<=len(data['items'])<=50
        items.extend(data['items']);offset=data['nextOffset']
    assert len(items)==len({row['id'] for row in items})==1257
    assert sum(row['isBranch'] is True for row in items)==521
    assert all(row['coverage']=='manual' for row in items)
    assert all(len(row['name'])<=160 for row in items if row['catalogOrigin']=='monitoring')
    assert client.get('/api/v1/universities',params={'offset':-1}).status_code==422


def test_region_and_name_tokens_find_branches_without_guessing_automatic_coverage(client):
    data=client.get('/api/v1/universities',params={'q':'  САРАТОВСКАЯ   ЧЕРНЫШЕВСКОГО '}).json()
    assert data['total']>=2
    assert all('саратовская' in item['region'].casefold() and 'чернышевского' in item['legalName'].casefold() for item in data['items'])
    assert any(item['isBranch'] for item in data['items'])
    assert all(item['coverage']=='manual' for item in data['items'])
