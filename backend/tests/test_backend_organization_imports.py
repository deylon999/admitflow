"""Compatibility for backend imports independently of HTTP contract snapshots."""

import importlib
from unittest.mock import patch

import pytest


MODULES = (
    ('config', 'core.config'),
    ('http', 'core.http'),
    ('schema_base', 'core.schema_base'),
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
