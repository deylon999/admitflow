import pytest
import json
from test_api import start, WATCH, HEADERS


@pytest.mark.parametrize('field',['university','title','sourceUrl'])
@pytest.mark.parametrize('control',['\x00','\n','\x7f'])
def test_control_characters_are_rejected_before_normalization(client,field,control):
    start(client)
    response=client.post('/api/v1/watches',json=WATCH|{field:WATCH[field]+control},headers=HEADERS)
    assert response.status_code==422
    assert client.get('/api/v1/watches').json()==[]


@pytest.mark.parametrize('case',['duplicate','nan','overflow','deep'])
def test_ambiguous_json_never_writes(client,case):
    start(client)
    body=json.dumps(WATCH)
    if case=='duplicate': body=body.replace('"title":','"title":"first","title":')
    if case=='nan': body=body.replace('120','NaN')
    if case=='overflow': body=body.replace('120','1e9999')
    if case=='deep': body='['*65+'0'+']'*65
    response=client.post('/api/v1/watches',content=body,headers=HEADERS|{'Content-Type':'application/json'})
    assert response.status_code==400
    assert client.get('/api/v1/watches').json()==[]


def test_json_brackets_inside_string_are_not_nesting(client):
    start(client)
    response=client.post('/api/v1/watches',json=WATCH|{'title':'['*80+']'*80},headers=HEADERS)
    assert response.status_code==201


def test_validation_errors_never_echo_input_or_unknown_keys(client):
    payload=WATCH['values']|{f'private-secret-{index}':'private-value' for index in range(100)}
    response=client.post('/api/v1/calculate',json=payload)
    assert response.status_code==422
    body=response.json()
    assert len(body['fields'])==20 and body['truncated'] is True
    assert 'private' not in response.text and 'input' not in response.text and 'ctx' not in response.text
    schema=client.get('/api/openapi.json').json()
    assert schema['paths']['/api/v1/calculate']['post']['responses']['422']['content']['application/json']['schema']['$ref'].endswith('/ValidationProblem')


@pytest.mark.parametrize('value',[1761955200,'2026-11-01T00:00:00','2026-11-01T00:00:00.1234567Z'])
def test_import_requires_explicit_iso_timestamps(client,value):
    start(client)
    client.post('/api/v1/watches',json=WATCH,headers=HEADERS).raise_for_status()
    bundle=client.get('/api/v1/export').json()
    bundle['exportedAt']=value
    response=client.post('/api/v1/import',json={'bundle':bundle},headers=HEADERS|{'Idempotency-Key':'timestamp-case'})
    assert response.status_code==422 and len(client.get('/api/v1/watches').json())==1
