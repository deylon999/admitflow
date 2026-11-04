import json
import logging
from uuid import UUID

from sqlalchemy.exc import OperationalError
from sqlalchemy import text
import pytest


def test_request_id_and_logs_do_not_include_user_data(client,caplog):
    with caplog.at_level(logging.INFO,logger='admitflow.http'):
        response=client.get('/api/v1/watches/private-id?token=private-query',headers={'X-Request-ID':'private-client-id','Cookie':'secret=private-cookie'})
    assert response.status_code==401
    UUID(response.headers['x-request-id'])
    assert response.headers['x-request-id']!='private-client-id'
    record=json.loads(caplog.records[-1].message)
    assert record['route']=='/api/v1/watches/{watch_id}'
    assert record['status']==401 and record['durationMs']>=0
    assert all(value not in caplog.text for value in ['private-id','private-query','private-cookie','private-client-id'])


def test_unexpected_exception_is_safe_and_has_request_id(client,application,caplog):
    @application.get('/api/test-failure')
    def failing():
        raise RuntimeError('private SQL password candidate ID')
    with caplog.at_level(logging.INFO,logger='admitflow.http'):
        response=client.get('/api/test-failure')
    assert response.status_code==500
    assert response.json()['requestId']==response.headers['x-request-id']
    assert 'private SQL' not in response.text+caplog.text


def test_liveness_is_independent_of_readiness(client,monkeypatch):
    def database_down(*args,**kwargs):
        raise OperationalError('private SQL',{},Exception('private db path'))
    monkeypatch.setattr('sqlalchemy.orm.Session.execute',database_down)
    assert client.get('/api/live').status_code==200
    for url in ['/api/health','/api/ready']:
        response=client.get(url)
        assert response.status_code==503 and 'private' not in response.text
        assert 'x-request-id' in response.headers


@pytest.mark.parametrize('revision',['0001','future',None])
def test_readiness_rejects_incompatible_or_empty_revision(client,application,revision):
    with application.state.engine.begin() as db:
        db.execute(text('DELETE FROM alembic_version'))
        if revision is not None:
            db.execute(text('INSERT INTO alembic_version VALUES (:revision)'),{'revision':revision})
    assert client.get('/api/live').status_code==200
    for path in ['/api/ready','/api/health']:
        response=client.get(path)
        assert response.status_code==503 and 'alembic_version' not in response.text
    with application.state.engine.connect() as db:
        assert db.execute(text('SELECT version_num FROM alembic_version')).scalars().all()==([] if revision is None else [revision])


def test_missing_revision_table_is_not_ready_and_not_created(client,application):
    with application.state.engine.begin() as db:
        db.execute(text('DROP TABLE alembic_version'))
    assert client.get('/api/ready').status_code==503
    assert client.get('/api/live').status_code==200
    with application.state.engine.connect() as db:
        assert not db.execute(text("SELECT 1 FROM sqlite_master WHERE name='alembic_version'")).first()


def test_connection_pool_exhaustion_is_retryable_not_internal_error(client,monkeypatch):
    from sqlalchemy.exc import TimeoutError as PoolTimeout
    def busy(*args,**kwargs):
        raise PoolTimeout('QueuePool limit reached, private pool detail')
    monkeypatch.setattr('sqlalchemy.orm.Session.scalar',busy)
    monkeypatch.setattr('sqlalchemy.orm.Session.execute',busy)
    response=client.get('/api/v1/watches',headers={'Cookie':'abiturient_session=x'})
    assert response.status_code==503 and response.headers['retry-after']=='5' and 'private' not in response.text
