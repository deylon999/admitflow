"""Verified public metadata, isolation, import atomicity and old API compatibility."""
import pytest

from app.accreditation_registry import load_registry
from app.national_catalog import load_catalog
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.admissions import Campaign, CompetitionGroup, Source
from app.catalog_import import import_reviewed
from app.config import Settings
from app.database import BrowserSession
from app.main import create_app
from native_support import postgres_engine  # noqa: F401

BASE = '/api/v1/catalog'


@pytest.fixture
def catalog(client, application):
    import_reviewed(application.state.engine)
    return client


def assert_catalog_path(client):
    result = client.get(BASE + '/universities', params={'q': 'СГУ Чернышевского'}).json()
    assert result['total'] == 1
    university = result['items'][0]
    assert university['id'] == 'sgu-saratov'
    assert university['years'] == [2026] and university['knownProgramCount'] == 2
    assert university['provenance']['edition'] == 2025
    assert university['provenance']['url'].endswith('inst.php?id=258')
    detail = client.get(BASE + '/universities/' + university['id']).json()
    assert detail == university
    programs = client.get(BASE + '/programs', params={'universityId': university['id'], 'year': 2026}).json()
    assert programs['total'] == 2 and programs['years'] == [2026]
    program = next(p for p in programs['items'] if p['code'] == '09.03.04')
    assert client.get(BASE + '/programs/' + program['id']).json() == program
    assert program['seats'] == 16 and program['year'] == 2026
    assert program['provenance']['kind'] == 'archive'
    assert program['provenance']['url'] == 'https://www.sgu.ru/svodka/4588'
    assert program['provenance']['verifiedAt'].startswith('2026-11-03')
    assert program['provenance']['sourceUpdatedAt'] is None
    assert len(program['provenance']['originalSha256']) == 64
    for field in ('forecast', 'examRequirements', 'historicalCutoff'):
        assert program[field] is None
    assert not {'entries', 'candidateKey', 'chance', 'position'} & program.keys()


def test_verified_university_to_program_path(catalog, application):
    assert_catalog_path(catalog)
    with Session(application.state.engine) as db:
        assert db.scalar(select(func.count()).select_from(BrowserSession)) == 0
        assert db.scalar(select(func.count()).select_from(Source)) == 0


def test_no_implicit_program_seed_or_demo_fallback(client):
    result = client.get(BASE + '/programs').json()
    assert result == {'items': [], 'total': 0, 'nextOffset': None, 'years': [], 'subjects': []}
    assert client.get(BASE + '/programs/mtuci-se').status_code == 404
    assert client.get(BASE + '/universities/mtuci').status_code == 404


def test_import_is_repeatable_without_activating_sources(catalog, application):
    before = catalog.get(BASE + '/programs').json()
    import_reviewed(application.state.engine)
    assert catalog.get(BASE + '/programs').json() == before
    assert catalog.get('/api/v1/groups').json()['total'] == 2
    # The legacy catalog remains intact and reachable.
    assert catalog.get('/api/v1/universities').json()['total'] == 1257


def test_year_subject_unknown_id_and_empty_search_do_not_invent_data(catalog):
    for params in ({'year': 2027}, {'subject': 'Информатика'}, {'universityId': 'unknown'}, {'q': 'missing'}):
        result = catalog.get(BASE + '/programs', params=params).json()
        assert result['items'] == [] and result['total'] == 0
    for path in ('/programs/unknown', '/universities/unknown'):
        assert catalog.get(BASE + path).status_code == 404


def test_unicode_search_region_sort_and_pagination(catalog):
    page = catalog.get(BASE + '/universities', params={'limit': 50}).json()
    # 1257 monitoring records plus organisations found only in the accreditation register (KAN-217).
    assert page['total'] == 1257 + len(load_registry().registry_only) and page['nextOffset'] == 50
    assert page['accreditationDate'] == '2026-11-10'
    second = catalog.get(BASE + '/universities', params={'limit': 50, 'offset': 50}).json()
    assert not {r['id'] for r in page['items']} & {r['id'] for r in second['items']}
    region = catalog.get(BASE + '/universities', params={'region': 'Саратовская область'}).json()
    assert region['items'] and all(r['region'] == 'Саратовская область' for r in region['items'])
    for term in ('ПРОГРАММНАЯ', '09.03.04'):
        assert catalog.get(BASE + '/programs', params={'q': term}).json()['total'] == 1
        assert catalog.get(BASE + '/universities', params={'q': term}).json()['items'][0]['id'] == 'sgu-saratov'
    first = catalog.get(BASE + '/programs', params={'limit': 1}).json()
    reverse = catalog.get(BASE + '/programs', params={'sort': 'name-desc', 'limit': 1}).json()
    assert first['items'][0]['id'] != reverse['items'][0]['id']
    assert catalog.get(BASE + '/universities?offset=100000').json()['items'] == []


@pytest.mark.parametrize('suffix', [
    '/programs?year=2026.5', '/programs?year=1999', '/programs?limit=51',
    '/programs?offset=-1', '/universities?sort=chance', '/universities?limit=0',
    '/programs?q=' + 'x' * 121,
])
def test_invalid_filter_bounds(client, suffix):
    assert client.get(BASE + suffix).status_code == 422


def test_modified_or_manual_metadata_never_promoted_to_verified(catalog, application):
    with Session(application.state.engine) as db:
        row = db.get(CompetitionGroup, 'sgu-2026-4588')
        row.seats = 999
        db.commit()
    assert catalog.get(BASE + '/programs/sgu-2026-4588').status_code == 404
    assert catalog.get(BASE + '/programs').json()['total'] == 1
    with pytest.raises(ValueError, match='catalog_identity_conflict'):
        import_reviewed(application.state.engine)


def test_import_conflict_rolls_back_entire_batch(application):
    with TestClient(application):
        import_reviewed(application.state.engine)
        with Session(application.state.engine) as db:
            db.delete(db.get(CompetitionGroup, 'sgu-2026-4588'))
            db.get(CompetitionGroup, 'sgu-2026-4576').seats = 999
            db.commit()
        with pytest.raises(ValueError):
            import_reviewed(application.state.engine)
        with Session(application.state.engine) as db:
            assert db.get(CompetitionGroup, 'sgu-2026-4588') is None
            assert db.scalar(select(func.count()).select_from(Campaign)) == 1


@pytest.mark.postgres
def test_native_postgres_catalog_path(postgres_engine):
    app = create_app(Settings(database_url=postgres_engine.url.render_as_string(hide_password=False), auto_create_schema=False))
    with TestClient(app) as client:
        import_reviewed(app.state.engine)
        assert_catalog_path(client)


def test_universities_show_accreditation_source_and_registry_only_records(catalog):
    registry = load_registry()
    sgu = catalog.get(BASE + '/universities/sgu-saratov').json()
    assert sgu['accreditation']['status'] == 'active' and sgu['accreditation']['ogrn'] == registry.by_catalog_id['258'].ogrn
    assert sgu['accreditation']['sourceUrl'] == 'https://isga.obrnadzor.gov.ru/accredreestr/opendata/'
    assert sgu['provenance']['kind'] == 'monitoring'
    only = registry.registry_only[0]
    record = catalog.get(BASE + '/universities/' + only.id).json()
    assert record['provenance']['kind'] == 'accreditation' and record['accreditation']['matchMethod'] == 'registry'
    assert record['knownProgramCount'] == 0 and record['years'] == [] and record['legalName'] == only.name
    page = catalog.get(BASE + '/universities', params={'q': only.ogrn[:0] + (only.short_name or only.name).split()[0]}).json()
    assert page['total'] >= 1
    branch = next(r for r in load_catalog().institutions if r.is_branch)
    assert catalog.get(BASE + '/universities/' + branch.id).json()['accreditation'] is None
