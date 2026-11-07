from dataclasses import replace

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_wrong_origin_and_host_never_create_session(client):
    for headers in [
        {'Origin':'https://evil.example'}, {'Origin':'null'},
        {'Origin':'http://testserver/extra'}, {'Origin':'http://user@testserver'},
        {'Sec-Fetch-Site':'cross-site'},
    ]:
        response=client.post('/api/v1/session',headers={'X-Requested-With':'abiturient'}|headers)
        assert response.status_code==403
        assert 'set-cookie' not in response.headers
    assert client.get('/api/health',headers={'Host':'evil.example'}).status_code==400
    assert client.post('/api/v1/session',headers={'X-Requested-With':'abiturient','Origin':'http://testserver'}).status_code==204


def test_public_origin_is_exact_including_scheme_and_port(tmp_path):
    settings=Settings(database_url=f"sqlite:///{tmp_path/'origin.db'}",allowed_hosts=('testserver',),public_origin='https://testserver:8443')
    with TestClient(create_app(settings)) as client:
        for origin in ['http://testserver:8443','https://testserver','https://testserver:8443.evil.org']:
            assert client.post('/api/v1/session',headers={'X-Requested-With':'abiturient','Origin':origin}).status_code==403
        assert client.post('/api/v1/session',headers={'X-Requested-With':'abiturient','Origin':'https://testserver:8443'}).status_code==204
        # There are no stateless calculator exceptions to the write-origin policy.
        assert client.post('/api/v1/calculate', headers={'X-Requested-With':'abiturient','Origin':'https://evil.example'}, json={}).status_code==403
