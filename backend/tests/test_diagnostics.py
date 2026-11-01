import json
import logging
from uuid import UUID

from sqlalchemy.exc import OperationalError


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
