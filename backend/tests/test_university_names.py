"""Conservative naming, immutable sources, additive contracts and real imports."""
from copy import deepcopy
from datetime import datetime, timezone
import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from app.accreditation_registry import load_registry
from app.admissions import University
from app.catalog_import import import_reviewed
from app.config import Settings
from app.main import create_app
from app.national_catalog import DEFAULT_PATH, import_snapshot, load_catalog
from app.product_catalog import universities
from app.product_catalog_schemas import Provenance
from app.university_name_report import build_report
from app.university_names import choose_name, identity, load_reviews, normalize_legal_name, parse_reviews, usable_short
from native_support import postgres_engine  # noqa: F401

BASE = '/api/v1/catalog/universities'


def choose(full_name, *, branch=False, reviews=None, registry_org=None):
    return choose_name(identifier='review-id', full_name=full_name, is_branch=branch,
                       provenance=Provenance(url='https://monitoring.miccedu.ru/', verified_at=datetime(2026, 11, 10, tzinfo=timezone.utc), kind='monitoring'),
                       source_sha256='a' * 64, reviews=reviews or {}, registry_org=registry_org, registry=load_registry())


@pytest.mark.parametrize('placeholder', [None, '', '-', '—', 'нет', 'отсутствует', 'не предусмотрено', 'не указано'])
def test_placeholders_never_become_official_names(placeholder):
    assert not usable_short(placeholder)


def test_real_federal_research_institute_academy_private_and_long_names_keep_identity():
    rows = load_catalog().institutions
    for category in ('федеральный университет', 'национальный исследовательский', 'институт', 'академия', 'частное'):
        examples = [row for row in rows if category in row.name.casefold() and not row.is_branch]
        assert examples, category
        for row in examples:
            value = normalize_legal_name(row.name, is_branch=False)
            if value:
                # Every identifying character is retained as a contiguous suffix,
                # including geography, honorary names and specialisation.
                assert value in ' '.join(row.name.split())
                assert len(value) < len(row.name)
                assert any(word in value.casefold() for word in ('университет', 'институт', 'академия', 'школа', 'консерватория'))
    assert any(len(row.name) > 250 for row in rows)


@pytest.mark.parametrize('name', [
    'Институт экономики имени А. А. Иванова в городе Москве',
    'Автомобильно-дорожный институт (филиал) федерального государственного бюджетного образовательного учреждения высшего образования «Донецкий национальный технический университет» в г. Горловка',
    'Ордена Трудового Красного Знамени Федеральное государственное бюджетное образовательное учреждение высшего образования «Московский технический университет связи и информатики»',
    'федеральное государственное бюджетное образовательное учреждение высшего образования «Институт» в г. Москве',
    'федеральное государственное бюджетное образовательное учреждение высшего образования «Институт «Мир»»',
    'федеральное государственное бюджетное образовательное учреждение высшего образования',
])
def test_ambiguous_names_abstain_without_deleting_any_words(name):
    assert normalize_legal_name(name, is_branch=False) is None
    assert choose(name).value == name


def test_no_branch_is_normalized_or_given_its_parents_abbreviation():
    registry = load_registry()
    head = registry.by_catalog_id['1593']
    for row in load_catalog().institutions:
        if row.is_branch:
            result = choose(row.name, branch=True, registry_org=head)
            assert result.value == row.name and result.kind == 'original'
            assert result.parent_name is None and result.city is None


def test_strict_source_identity_not_domain_or_fuzzy_join():
    head = load_registry().by_catalog_id['1593']
    row = next(row for row in load_catalog().institutions if row.registry_id == '1593')
    assert identity(row.name) == identity(head.name)
    assert choose(row.name, registry_org=head).value == 'МТУСИ'
    assert choose(row.name + ' имени другого человека', registry_org=head).kind == 'original'


def review_for(name, *, kind='manual', status='verified'):
    review = deepcopy(next(iter(load_reviews().values())))
    review.update(id='review-id', fullName=name, displayName='Проверенный институт', isBranch=False,
                  parentUniversityName=None, city=None, kind=kind, status=status)
    return {'review-id': review}


def test_priority_official_then_rules_then_reviewed_manual_then_original():
    name = 'федеральное государственное бюджетное образовательное учреждение высшего образования «Московский институт экономики имени Н. Н. Иванова»'
    manual = review_for(name)
    assert choose(name, reviews=manual).kind == 'normalized'
    assert choose(name, reviews=manual).value == 'Московский институт экономики имени Н. Н. Иванова'
    official = review_for(name, kind='official')
    assert choose(name, reviews=official).kind == 'official'
    plain = 'Полное исходное наименование без однозначного юридического префикса'
    assert choose(plain, reviews=review_for(plain)).kind == 'manual'
    for reviews in (review_for(plain, status='candidate'), review_for(plain + ' новое имя')):
        assert choose(plain, reviews=reviews).value == plain
        assert choose(plain, reviews=reviews).kind == 'original'


def test_reviewed_aliases_are_searchable_but_candidates_and_stale_reviews_are_not(client, monkeypatch):
    row = next(row for row in load_catalog().institutions if row.registry_id == '1593')
    # A unit-only alias exercises the contract, never enters the shipped dataset.
    reviews = review_for(row.name, kind='official')
    item = reviews.pop('review-id')
    item.update(id=row.id, aliases=['contract-only-alias'])
    reviews[row.id] = item
    monkeypatch.setattr('app.university_names.load_reviews', lambda: reviews)
    assert client.get(BASE, params={'q': 'contract-only-alias'}).json()['items'][0]['id'] == row.id
    for change in ({'status': 'candidate'}, {'fullName': row.name + ' changed'}):
        monkeypatch.setattr('app.university_names.load_reviews', lambda: {row.id: {**item, **change}})
        assert client.get(BASE, params={'q': 'contract-only-alias'}).json()['total'] == 0


def test_review_parser_requires_provenance_branch_identity_and_atomic_validation():
    review = next(iter(load_reviews().values()))
    for field, value in [('source', {**review['source'], 'sha256': 'wrong'}), ('isBranch', False), ('displayName', '-')]:
        with pytest.raises(ValueError):
            parse_reviews(json.dumps({'format': 'university-names-v1', 'records': [{**review, field: value}]}))
    with pytest.raises(ValueError, match='duplicate'):
        parse_reviews(json.dumps({'format': 'university-names-v1', 'records': [review, review]}))


def assert_names(client):
    row = client.get(BASE + '/miccedu-1593').json()
    assert row['displayName'] == 'МТУСИ'
    assert row['displayNameSource']['kind'] == 'official'
    assert row['displayNameSource']['sha256'] == load_registry().archive_sha256
    assert row['displayNameSource']['verifiedAt']
    branch = client.get(BASE + '/miccedu-140143824').json()
    assert branch['isBranch'] is True and branch['accreditation'] is None
    assert branch['displayName'] == 'Автомобильно-дорожный институт (филиал) ДонНТУ г.Горловка'
    assert branch['branchInfo']['parentUniversityName'] == 'Донецкий национальный технический университет'
    assert branch['branchInfo']['city'] == 'Горловка'
    for term in ('МТУСИ', 'московский технический университет связи', 'ордена трудового красного знамени'):
        ids, offset = set(), 0
        while offset is not None:
            page = client.get(BASE, params={'q': term, 'offset': offset, 'limit': 50}).json()
            ids.update(item['id'] for item in page['items'])
            offset = page['nextOffset']
        assert row['id'] in ids
    assert any(item['id'] == branch['id'] for item in client.get(BASE, params={'q': 'ДонНТУ Горловка'}).json()['items'])


def test_additive_dto_full_names_and_search_with_unchanged_legacy_api(client):
    assert_names(client)
    full = next(row for row in load_catalog().institutions if row.registry_id == '1593')
    row = client.get(BASE + '/' + full.id).json()
    assert row['legalName'] == full.name and row['name'] == full.name
    legacy = client.get('/api/v1/universities', params={'q': 'Московский технический'}).json()
    assert full.id in {item['id'] for item in legacy['items']}


def test_report_covers_every_real_record_and_has_honest_disjoint_counts(client, application):
    with Session(application.state.engine) as db:
        rows = universities(db)
    report = build_report(rows)
    assert report['total'] == len(load_catalog().institutions) + len(load_registry().registry_only)
    assert sum(report[key] for key in ('official', 'normalized', 'manual', 'original')) == report['total']
    assert report['needsManualReview'] == report['original'] == len(report['manualReviewIds'])
    assert report['branches'] == 521 and report['branchesWithVerifiedMetadata'] == 1
    assert len({row.id for row in rows}) == len(rows)
    for row in rows:
        source = row.display_name_source
        assert source.sha256 and source.url and source.verified_at
        if source.kind == 'original':
            assert row.display_name == row.legal_name
        if row.is_branch and not row.branch_info:
            assert row.display_name == row.legal_name


def assert_repeatable(engine, client, tmp_path):
    before = client.get(BASE + '/miccedu-140143824').json()
    reviews_before = deepcopy(load_reviews())
    import_reviewed(engine)
    with Session(engine) as db:
        imported = db.scalars(select(University)).all()
        before_db = [(row.id, row.name, row.parent_id, row.search_name) for row in imported]
    import_reviewed(engine)
    target = tmp_path / 'reimported.json'
    import_snapshot(DEFAULT_PATH, target)
    import_snapshot(DEFAULT_PATH, target)
    assert target.read_bytes() == DEFAULT_PATH.read_bytes()
    assert client.get(BASE + '/miccedu-140143824').json() == before
    assert load_reviews() == reviews_before
    with Session(engine) as db:
        assert [(row.id, row.name, row.parent_id, row.search_name) for row in db.scalars(select(University))] == before_db
    assert 'display_name' not in {col['name'] for col in inspect(engine).get_columns('universities')}


def test_import_preserves_review_overlay_and_original_data(client, application, tmp_path):
    assert_repeatable(application.state.engine, client, tmp_path)


@pytest.mark.postgres
def test_native_postgres_names_search_import_and_schema(postgres_engine, tmp_path):
    app = create_app(Settings(database_url=postgres_engine.url.render_as_string(hide_password=False), auto_create_schema=False))
    with TestClient(app) as client:
        assert_names(client)
        assert_repeatable(app.state.engine, client, tmp_path)
