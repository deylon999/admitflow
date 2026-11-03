"""Migrated, isolated PostgreSQL fixture shared by native runtime suites."""
import os

import pytest

from app.migrations import upgrade_schema
from pg_support import isolated_postgres


@pytest.fixture
def postgres_engine():
    if not os.getenv('TEST_DATABASE_URL'):
        pytest.skip('Requires a disposable PostgreSQL test database')
    with isolated_postgres(os.environ['TEST_DATABASE_URL']) as engine:
        upgrade_schema(engine)
        yield engine
