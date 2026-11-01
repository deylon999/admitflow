from datetime import datetime,timedelta,timezone
from uuid import UUID
from test_api import start,create,VALUES,HEADERS


def test_export_clock_regression_refuses_instead_of_emitting_invalid_dates(client,monkeypatch):
    now=datetime(2026,11,1,23,tzinfo=timezone.utc)
    monkeypatch.setattr('app.main.utcnow',lambda:now)
    start(client)
    watch=create(client)
    original=client.get(f"/api/v1/watches/{watch['id']}").json()
    monkeypatch.setattr('app.main.utcnow',lambda:now-timedelta(microseconds=1))
    response=client.get('/api/v1/export')
    assert response.status_code==409
    assert 'exportedAt' not in response.json()
    assert client.get(f"/api/v1/watches/{watch['id']}").json()==original
    monkeypatch.setattr('app.main.utcnow',lambda:now)
    response=client.get('/api/v1/export')
    assert response.status_code==200
    assert response.json()['watches']==[original]


def test_equal_time_updates_are_latest_without_changing_observed_time(client,monkeypatch):
    now=datetime(2026,11,1,23,tzinfo=timezone.utc)
    monkeypatch.setattr('app.main.utcnow',lambda:now)
    monkeypatch.setattr('app.main.uuid4',lambda:UUID(int=1))
    start(client)
    watch=create(client)
    for rank in (121,122):
        response=client.post(f"/api/v1/watches/{watch['id']}/snapshots",json=VALUES|{'rank':rank},headers=HEADERS)
        assert response.status_code==201
    history=client.get(f"/api/v1/watches/{watch['id']}").json()['history']
    assert [item['values']['rank'] for item in history]==[122,121,120]
    assert len({item['capturedAt'] for item in history})==1
    monkeypatch.setattr('app.main.utcnow',lambda:now-timedelta(seconds=1))
    refused=client.post(f"/api/v1/watches/{watch['id']}/snapshots",json=VALUES,headers=HEADERS)
    assert refused.status_code==409
    assert len(client.get(f"/api/v1/watches/{watch['id']}").json()['history'])==3
