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
