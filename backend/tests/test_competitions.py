"""KAN-228: a published list is readable in official order without any candidate identifiers."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.admissions import CandidateEntry
from test_api import HEADERS, start
from test_sgu_adapter import BINDING
from test_source_lookup import lookup_context  # noqa: F401
from test_subscriptions import confirm

GROUP = BINDING.group_id


def test_list_metadata_marks_archive_and_unpublished_priorities(lookup_context):
    client, app = lookup_context
    value = client.get(f'/api/v1/competitions/{GROUP}').json()
    assert value['groupId'] == GROUP and value['year'] == 2026
    assert value['snapshot']['kind'] == 'archive' and value['snapshot']['complete'] is True
    assert value['snapshot']['rowCount'] == 573 and value['snapshot']['sourceUrl'].startswith('https://www.sgu.ru/')
    assert 'archive' in value['warnings'] and value['myRank'] is None
    assert value['history'][0]['published'] is True
    with Session(app.state.engine) as db:
        known = db.scalar(select(func.count()).select_from(CandidateEntry).where(CandidateEntry.priority.is_not(None)))
    assert value['prioritiesPublished'] == (known > 0)
    assert ('priorities_not_published' in value['warnings']) == (known == 0)
    assert client.get('/api/v1/competitions/missing').status_code == 404


def test_rows_follow_official_order_and_never_expose_identifiers(lookup_context):
    client, app = lookup_context
    page = client.get(f'/api/v1/competitions/{GROUP}/rows').json()
    ranks = [row['officialRank'] for row in page['items']]
    assert ranks == list(range(1, 51)) and page['total'] == 573 and page['nextOffset'] == 50
    text = client.get(f'/api/v1/competitions/{GROUP}/rows', params={'limit': 50, 'offset': 500}).text
    for private in ('candidateKey', 'rowRef', 'FIXTURE-', 'publicCode'):
        assert private not in text
    last = client.get(f'/api/v1/competitions/{GROUP}/rows', params={'offset': 550}).json()
    assert last['nextOffset'] is None and last['items'][-1]['officialRank'] == 573
    reverse = client.get(f'/api/v1/competitions/{GROUP}/rows', params={'order': 'official-desc', 'limit': 3}).json()
    assert [r['officialRank'] for r in reverse['items']] == [573, 572, 571]
    jump = client.get(f'/api/v1/competitions/{GROUP}/rows', params={'rankFrom': 100, 'limit': 1}).json()
    assert jump['items'][0]['officialRank'] == 100 and jump['total'] == 474
    assert client.get(f'/api/v1/competitions/{GROUP}/rows', params={'limit': 51}).status_code == 422
    assert client.get(f'/api/v1/competitions/{GROUP}/rows', params={'order': 'score'}).status_code == 422


def test_filters_match_database_counts(lookup_context):
    client, app = lookup_context
    with Session(app.state.engine) as db:
        def count(*where):
            return db.scalar(select(func.count()).select_from(CandidateEntry).where(*where))
        expected = dict(yes=count(CandidateEntry.consent.is_(True)), no=count(CandidateEntry.consent.is_(False)), unknown=count(CandidateEntry.consent.is_(None)))
        first = count(CandidateEntry.priority == 1)
    for value, total in expected.items():
        assert client.get(f'/api/v1/competitions/{GROUP}/rows', params={'consent': value}).json()['total'] == total
    assert client.get(f'/api/v1/competitions/{GROUP}/rows', params={'priority': 'first'}).json()['total'] == first
    summary = client.get(f'/api/v1/competitions/{GROUP}/summary').json()
    assert summary['byConsent'] == expected and summary['total'] == 573
    assert sum(b['count'] for b in summary['scoreBins']) == summary['scoreKnown']
    lowers = [b['lower'] for b in summary['scoreBins']]
    assert lowers == list(range(lowers[0], lowers[-1] + 10, 10))
    assert summary['myRank'] is None and summary['aboveMe'] is None


def test_only_the_guest_sees_their_own_row(lookup_context):
    from fastapi.testclient import TestClient
    client, app = lookup_context
    start(client)
    assert client.post('/api/v1/subscriptions', json=confirm(client, 3), headers=HEADERS).status_code == 201
    value = client.get(f'/api/v1/competitions/{GROUP}').json()
    assert value['myRank'] == 3
    rows = client.get(f'/api/v1/competitions/{GROUP}/rows', params={'limit': 5}).json()['items']
    assert [r['mine'] for r in rows] == [False, False, True, False, False]
    summary = client.get(f'/api/v1/competitions/{GROUP}/summary').json()
    assert summary['myRank'] == 3 and summary['aboveMe']['total'] == 2
    with TestClient(app) as other:
        assert other.get(f'/api/v1/competitions/{GROUP}').json()['myRank'] is None
        start(other)
        assert not any(r['mine'] for r in other.get(f'/api/v1/competitions/{GROUP}/rows', params={'limit': 5}).json()['items'])
    # An expired or forged cookie reads the public list without failing.
    client.cookies.set('abiturient_session', 'forged', path='/api')
    assert client.get(f'/api/v1/competitions/{GROUP}/rows', params={'limit': 1}).status_code == 200
