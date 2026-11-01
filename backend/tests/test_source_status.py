from dataclasses import replace
from datetime import timedelta

from sqlalchemy.orm import Session

from app.admissions import Source
from app.sources.publishing import publish, record_failure
from app.sources.registry import Registry
from app.sources.status import source_status
from app.sources.storage import RawStore
from source_helpers import NOW, parsed, raw, registry, seed_source


def test_archive_and_failures_never_look_fresh(source_engine,tmp_path):
    seed_source(source_engine)
    store=RawStore(tmp_path/'raw')
    snapshot=publish(source_engine,'source-1',parsed(),raw(),store,registry=registry(),allow_unattested=True)
    with Session(source_engine) as db:
        state=source_status(db,'source-1',now=NOW)
        assert state['state']=='archived' and state['dataKind']=='archive'
        assert state['sourceUpdatedAt'] is None and state['assessmentAvailable'] is False
    record_failure(source_engine,'source-1','incomplete_list',NOW+timedelta(minutes=1))
    with Session(source_engine) as db:
        state=source_status(db,'source-1',now=NOW+timedelta(minutes=2))
        assert state['state']=='quarantined' and state['dataKind']=='archive'
        assert state['publishedSnapshotId']==snapshot and state['lastSuccessfulCheckAt']==NOW
    record_failure(source_engine,'source-1','network_error',NOW+timedelta(minutes=2))
    with Session(source_engine) as db:
        assert source_status(db,'source-1',now=NOW)['state']=='source_error'
        db.get(Source,'source-1').enabled=False
        db.commit()
        assert source_status(db,'source-1',now=NOW)['state']=='disabled'


def test_live_fresh_stale_unsupported_and_old_season(source_engine,tmp_path):
    seed_source(source_engine,snapshot_kind='live')
    attested=Registry((replace(registry()._adapters['synthetic-v1'],attested=True),))
    publish(source_engine,'source-1',parsed().model_copy(update={'kind':'live'}),raw(),RawStore(tmp_path/'raw'),registry=attested)
    with Session(source_engine) as db:
        assert source_status(db,'source-1',now=NOW,registry=attested)['state']=='fresh'
        assert source_status(db,'source-1',now=NOW+timedelta(minutes=31),registry=attested)['state']=='stale'
        assert source_status(db,'source-1',now=NOW)['state']=='unsupported'
        assert source_status(db,'source-1',now=NOW.replace(year=2027),registry=attested)['state']=='archived'
    record_failure(source_engine,'source-1','network_error',NOW-timedelta(minutes=1))
    with Session(source_engine) as db:
        assert db.get(Source,'source-1').last_error_code is None


def test_public_status_is_bounded_and_does_not_return_rows(client,application):
    seed_source(application.state.engine)
    response=client.get('/api/v1/sources/source-1/status')
    assert response.status_code==200
    body=response.json()
    assert body['season']==2026 and body['assessmentAvailable'] is False
    assert 'entries' not in body and 'payloadHash' not in body and 'lastErrorCode' not in body
    assert client.get('/api/v1/sources/unknown/status').status_code==404
