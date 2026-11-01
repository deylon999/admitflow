from contextlib import contextmanager
import re
from unittest.mock import Mock

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine import make_url

from pg_support import disposable_postgres_url, isolated_postgres


@pytest.mark.parametrize('value', ['sqlite:///admitflow_test.db', 'postgresql://user:secret@localhost/production', 'not-a-url'])
def test_unsafe_database_rejected_without_exposing_input(value):
    with pytest.raises(ValueError) as error:
        disposable_postgres_url(value)
    assert 'secret' not in str(error.value)


@pytest.mark.parametrize('failure', ['none', 'body', 'scoped-engine', 'create-schema'])
def test_only_new_schema_is_owned_and_cleaned(monkeypatch, failure):
    statements, urls = [], []
    admin, scoped = Mock(), Mock()
    @contextmanager
    def begin():
        connection = Mock()
        def execute(statement):
            statements.append(str(statement.compile(dialect=postgresql.dialect())))
            if failure == 'create-schema' and len(statements) == 1:
                raise RuntimeError('create refused')
        connection.execute.side_effect = execute
        yield connection
    admin.begin.side_effect = begin
    def make(value):
        urls.append(make_url(value))
        if len(urls) == 2 and failure == 'scoped-engine':
            raise RuntimeError('scoped refused')
        return admin if len(urls) == 1 else scoped
    monkeypatch.setattr('pg_support.make_engine', make)
    def run():
        with isolated_postgres('postgresql+psycopg://user:secret@localhost/admitflow_test') as engine:
            assert engine is scoped
            if failure == 'body':
                raise RuntimeError('body refused')
    if failure == 'none':
        run()
    else:
        with pytest.raises(RuntimeError):
            run()
    assert re.fullmatch(r'CREATE SCHEMA admitflow_test_[a-f0-9]{32}', statements[0])
    if failure == 'create-schema':
        assert len(statements) == 1  # Never drop a schema we failed to create.
    else:
        assert statements[1] == statements[0].replace('CREATE', 'DROP') + ' CASCADE'
        assert urls[1].query['options'] == '-csearch_path=' + statements[0].split()[-1]
    assert all('public' not in sql for sql in statements)
    admin.dispose.assert_called_once()
    if failure in ('none', 'body'):
        scoped.dispose.assert_called_once()
