import json
import sqlite3

from fastapi.testclient import TestClient
import pytest

from app.backup import BackupError, create_backup, file_hash, restore_backup, verify_backup
from app.config import Settings
from app.main import create_app
from app.sources.storage import RawStore
from app.sources.publishing import publish
from source_helpers import parsed, raw, registry, seed_source
from test_api import create, start


def test_restored_database_retains_ids_history_and_owner_isolation(client,application,tmp_path):
    start(client)
    watch=create(client)
    cookie=client.cookies.get('abiturient_session')
    store=RawStore(tmp_path/'raw')
    seed_source(application.state.engine)
    publish(application.state.engine,'source-1',parsed(),raw(),store,registry=registry(),allow_unattested=True)
    folder=create_backup(application.state.engine,store,tmp_path/'backups')
    restored=restore_backup(folder,tmp_path/'restored')
    assert file_hash(restored/'database.sqlite3')==file_hash(folder/'database.sqlite3')
    assert RawStore(restored/'raw').read(raw().payload_hash)==raw().body
    app=create_app(Settings(database_url=f"sqlite:///{restored/'database.sqlite3'}"))
    with TestClient(app) as recovered:
        recovered.cookies.set('abiturient_session',cookie)
        response=recovered.get(f"/api/v1/watches/{watch['id']}")
        assert response.status_code==200 and len(response.json()['history'])==1
        assert response.json()['latest']['calculation']['place']==watch['latest']['calculation']['place']
        recovered.cookies.clear()
        start(recovered)
        assert recovered.get(f"/api/v1/watches/{watch['id']}").status_code==404


def test_restore_refuses_overwrite_and_corruption(client,application,tmp_path):
    folder=create_backup(application.state.engine,RawStore(tmp_path/'raw'),tmp_path/'backups')
    destination=tmp_path/'existing'
    destination.mkdir()
    marker=destination/'keep.txt'
    marker.write_text('keep')
    with pytest.raises(BackupError,match='destination_exists'):
        restore_backup(folder,destination)
    assert marker.read_text()=='keep'
    with (folder/'database.sqlite3').open('ab') as file:
        file.write(b'corrupt')
    with pytest.raises(BackupError,match='hash_mismatch'):
        restore_backup(folder,tmp_path/'failed')
    assert not (tmp_path/'failed').exists()
    assert not any(path.name.startswith('.writing-') for path in tmp_path.iterdir())


def test_manifest_reference_tampering_and_database_integrity(client,application,tmp_path):
    folder=create_backup(application.state.engine,RawStore(tmp_path/'raw'),tmp_path/'backups')
    path=folder/'manifest.json'
    original=json.loads(path.read_text())
    path.write_text(json.dumps(original|{'rawHashes':['f'*64]}))
    with pytest.raises(BackupError,match='references_mismatch'):
        verify_backup(folder)
    with sqlite3.connect(folder/'database.sqlite3') as db:
        db.execute("CREATE VIEW unexpected AS SELECT 'private'")
    path.write_text(json.dumps(original|{'databaseHash':file_hash(folder/'database.sqlite3')}))
    with pytest.raises(BackupError,match='unexpected_backup_schema'):
        verify_backup(folder)
