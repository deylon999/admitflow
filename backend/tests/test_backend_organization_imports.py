"""Compatibility for backend imports independently of HTTP contract snapshots."""

import importlib
from unittest.mock import patch

import pytest


MODULES = (
    ('config', 'core.config'),
    ('http', 'core.http'),
    ('schema_base', 'core.schema_base'),
    ('accreditation_registry', 'catalog.accreditation_registry'),
    ('catalog_identity', 'catalog.catalog_identity'),
    ('catalog_import', 'catalog.catalog_import'),
    ('catalog_lock', 'catalog.catalog_lock'),
    ('coverage', 'catalog.coverage'),
    ('exam_requirements', 'catalog.exam_requirements'),
    ('national_catalog', 'catalog.national_catalog'),
    ('national_coverage', 'catalog.national_coverage'),
    ('product_catalog', 'catalog.product_catalog'),
    ('product_catalog_schemas', 'catalog.product_catalog_schemas'),
    ('program_catalog_batch', 'catalog.program_catalog_batch'),
    ('program_catalog_batch_fetch', 'catalog.program_catalog_batch_fetch'),
    ('program_catalog_import', 'catalog.program_catalog_import'),
    ('program_catalog_models', 'catalog.program_catalog_models'),
    ('program_catalog_review', 'catalog.program_catalog_review'),
    ('program_catalog_sources', 'catalog.program_catalog_sources'),
    ('source_catalog', 'catalog.source_catalog'),
    ('university_name_report', 'catalog.university_name_report'),
    ('university_names', 'catalog.university_names'),
    ('calculation', 'competitions.calculation'),
    ('competition_api', 'competitions.competition_api'),
    ('scenario_api', 'competitions.scenario_api'),
    ('scenario_explanations', 'competitions.scenario_explanations'),
    ('scenario_storage', 'competitions.scenario_storage'),
    ('scenarios', 'competitions.scenarios'),
)


@pytest.mark.parametrize(('legacy', 'target'), MODULES)
def test_legacy_module_resolves_to_canonical_module(legacy, target):
    old_name = f'app.{legacy}'
    old = importlib.import_module(old_name)
    new = importlib.import_module(f'app.{target}')
    assert old is new
    # String-based patch and monkeypatch therefore resolve the same globals.
    with patch(f'{old_name}._compatibility_probe', create=True) as probe:
        assert new._compatibility_probe is probe


def test_database_registry_and_factory_are_shared():
    from app import database
    from app.core import database as core

    assert database.Base is core.Base
    assert database.make_engine is core.make_engine
    for model in (database.BrowserSession, database.Watch, database.Snapshot,
                  database.LookupBudget, database.OperationRecord):
        assert model.registry is core.Base.registry
        assert core.Base.metadata.tables[model.__tablename__] is model.__table__
