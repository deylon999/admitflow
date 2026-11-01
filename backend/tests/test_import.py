import copy
from datetime import timedelta

import pytest
from sqlalchemy.orm import Session

from app.database import Snapshot
from app.calculation import CalculationInput, calculate
from test_api import create, start

HEADERS={'X-Requested-With':'abiturient','Idempotency-Key':'import-key-0001'}


def exported(client):
    start(client)
    watch=create(client)
    client.post(f"/api/v1/watches/{watch['id']}/snapshots",headers={'X-Requested-With':'abiturient'},json={'rank':12,'seats':5,'excluded':1,'noConsent':1})
    bundle=client.get('/api/v1/export').json()
    client.cookies.clear()
    start(client)
    return bundle


def test_import_isolated_atomic_replay_preserves_dates_and_new_ids(client):
    bundle=exported(client)
    response=client.post('/api/v1/import',headers=HEADERS,json={'bundle':bundle})
    assert response.status_code==201 and response.json()=={'importedCount':1,'snapshotCount':2,'replayed':False}
    saved=client.get('/api/v1/watches').json()
    assert len(saved)==1 and saved[0]['id']!=bundle['watches'][0]['id']
    assert client.get(f"/api/v1/watches/{bundle['watches'][0]['id']}").status_code==404
    history=client.get(f"/api/v1/watches/{saved[0]['id']}").json()['history']
    assert [row['values'] for row in history]==[row['values'] for row in bundle['watches'][0]['history']]
    assert [row['capturedAt'] for row in history]==[row['capturedAt'] for row in bundle['watches'][0]['history']]
    assert client.post('/api/v1/import',headers=HEADERS,json={'bundle':bundle}).json()['replayed'] is True
    assert len(client.get('/api/v1/watches').json())==1
    client.delete(f"/api/v1/watches/{saved[0]['id']}",headers={'X-Requested-With':'abiturient'})
    assert client.post('/api/v1/import',headers=HEADERS,json={'bundle':bundle}).json()['replayed'] is True
    assert client.get('/api/v1/watches').json()==[]


@pytest.mark.parametrize('change',['formula','url','model','future','duplicate'])
def test_invalid_file_never_partially_imports(client,change):
    bundle=exported(client)
    watch=bundle['watches'][0]
    if change=='formula':
        watch['history'][-1]['calculation']['place']=999
    elif change=='url':
        watch['sourceUrl']='javascript:alert(1)'
    elif change=='model':
        watch['history'][-1]['modelVersion']='automatic'
    elif change=='future':
        bundle['exportedAt']='2099-01-01T00:00:00Z'
    else:
        bundle['watches'].append(copy.deepcopy(watch))
    assert client.post('/api/v1/import',headers=HEADERS,json={'bundle':bundle}).status_code==422
    assert client.get('/api/v1/watches').json()==[]


def test_limits_mandatory_key_and_conflicting_retry(client):
    bundle=exported(client)
    assert client.post('/api/v1/import',headers={'X-Requested-With':'abiturient'},json={'bundle':bundle}).status_code==400
    for _ in range(20):
        create(client)
    assert client.post('/api/v1/import',headers=HEADERS,json={'bundle':bundle}).status_code==409
    assert len(client.get('/api/v1/watches').json())==20


def test_mid_import_database_failure_rolls_back_every_row(client,monkeypatch):
    bundle=exported(client)
    original=Session.flush
    def fail(db,*args,**kwargs):
        if any(isinstance(row,Snapshot) for row in db.new):
            raise RuntimeError('simulated write failure')
        return original(db,*args,**kwargs)
    with monkeypatch.context() as patch:
        patch.setattr(Session,'flush',fail)
        assert client.post('/api/v1/import',headers=HEADERS,json={'bundle':bundle}).status_code==500
    assert client.get('/api/v1/watches').json()==[]
    assert client.post('/api/v1/import',headers=HEADERS,json={'bundle':bundle}).status_code==201


def test_conflicting_retry_cannot_import_changed_file(client):
    bundle=exported(client)
    assert client.post('/api/v1/import',headers=HEADERS,json={'bundle':bundle}).status_code==201
    bundle['watches'][0]['title']='Changed title'
    assert client.post('/api/v1/import',headers=HEADERS,json={'bundle':bundle}).status_code==409
    assert len(client.get('/api/v1/watches').json())==1


def test_500_equal_timestamp_records_preserve_order_and_501_is_rejected(client):
    bundle=exported(client)
    watch=bundle['watches'][0]
    template=watch['latest']
    history=[]
    for index in range(500):
        values=CalculationInput(rank=index+1,seats=5,excluded=0,no_consent=0)
        history.append(template|{'id':f'external-{500-index:04d}','values':values.model_dump(by_alias=True),'calculation':calculate(values).model_dump(by_alias=True)})
    watch.update(history=history,latest=history[0])
    assert client.post('/api/v1/import',headers=HEADERS,json={'bundle':bundle}).json()['snapshotCount']==500
    saved=client.get('/api/v1/watches').json()[0]
    result=client.get('/api/v1/export').json()['watches'][0]['history']
    assert [row['values']['rank'] for row in result]==list(range(1,501))
    watch['history'].append(history[-1])
    assert client.post('/api/v1/import',headers=HEADERS|{'Idempotency-Key':'different-file-key'},json={'bundle':bundle}).status_code==422
