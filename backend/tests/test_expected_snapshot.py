from test_api import start, create, VALUES, HEADERS


def test_stale_expected_snapshot_refuses_atomically_and_cached_replay_still_works(client):
    start(client)
    watch=create(client)
    path=f"/api/v1/watches/{watch['id']}/snapshots"
    headers=HEADERS|{'X-Expected-Snapshot':watch['latest']['id'],'Idempotency-Key':'expected-update-001'}
    first=client.post(path,json=VALUES|{'rank':121},headers=headers)
    assert first.status_code==201
    newer=client.post(path,json=VALUES|{'rank':122},headers=HEADERS)
    assert newer.status_code==201
    replay=client.post(path,json=VALUES|{'rank':121},headers=headers)
    assert replay.status_code==201 and replay.json()==first.json()
    stale=client.post(path,json=VALUES|{'rank':123},headers=headers|{'Idempotency-Key':'expected-update-002'})
    assert stale.status_code==409
    detail=client.get(f"/api/v1/watches/{watch['id']}").json()
    assert detail['latest']['id']==newer.json()['id'] and len(detail['history'])==3
    accepted=client.post(path,json=VALUES|{'rank':123},headers=headers|{'Idempotency-Key':'expected-update-002','X-Expected-Snapshot':newer.json()['id']})
    assert accepted.status_code==201


def test_malformed_expected_snapshot_is_not_a_write(client):
    start(client)
    watch=create(client)
    path=f"/api/v1/watches/{watch['id']}/snapshots"
    for expected in ('', 'x'*101, ' leading'):
        assert client.post(path,json=VALUES,headers=HEADERS|{'X-Expected-Snapshot':expected}).status_code==400
    assert len(client.get(f"/api/v1/watches/{watch['id']}").json()['history'])==1
