from fastapi.testclient import TestClient
from test_api import HEADERS,start
from test_source_lookup import lookup_context
from test_subscriptions import confirm


def test_archive_export_is_private_bounded_factual_and_not_a_bearer_backup(lookup_context):
    client,app=lookup_context
    assert client.get('/api/v1/archive-export').status_code==401
    start(client);saved=client.post('/api/v1/subscriptions',json=confirm(client),headers=HEADERS).json()
    result=client.get('/api/v1/archive-export');data=result.json()
    assert result.status_code==200 and data['formatVersion']=='archive-facts-v1' and data['scope']=='current-published-facts'
    assert data['directions']==client.get('/api/v1/subscriptions').json()
    assert data['directions'][0]['id']==saved['id'] and data['directions'][0]['group']['snapshotId']
    for forbidden in ('FIXTURE-','candidateKey','ownerHash','confirmationToken','tokenHash','cookie'):
        assert forbidden not in result.text
    with TestClient(app) as other:
        start(other);assert other.get('/api/v1/archive-export').json()['directions']==[]
    assert client.delete(f"/api/v1/subscriptions/{saved['id']}",headers=HEADERS).status_code==204
    assert client.get('/api/v1/archive-export').json()['directions']==[]
