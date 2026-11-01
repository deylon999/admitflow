from app.main import COOKIE, token_hash
from test_api import start, HEADERS


def test_draft_scope_is_stable_one_way_isolated_and_not_an_api_credential(client):
    start(client)
    token=client.cookies.get(COOKIE)
    first=client.get('/api/v1/session').json()
    assert len(first['draftScope'])==64
    assert first==client.get('/api/v1/session').json()
    assert first['draftScope'] not in (token,token_hash(token))
    assert token not in str(first) and token_hash(token) not in str(first)
    client.cookies.clear()
    client.cookies.set(COOKIE,first['draftScope'],domain='testserver.local',path='/api')
    assert client.get('/api/v1/watches').status_code==401
    client.cookies.clear()
    start(client)
    assert client.get('/api/v1/session').json()['draftScope']!=first['draftScope']
    assert client.delete('/api/v1/session',headers=HEADERS).status_code==204
    start(client)
    assert client.get('/api/v1/session').json()['draftScope']!=first['draftScope']
