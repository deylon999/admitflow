import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import threading

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


def test_two_restores_reserve_destination_without_overwrite(client,application,tmp_path,monkeypatch):
    store=RawStore(tmp_path/'raw')
    first=create_backup(application.state.engine,store,tmp_path/'backups')
    second=create_backup(application.state.engine,store,tmp_path/'backups')
    target=tmp_path/'contended'
    barrier=threading.Barrier(2)
    original=Path.mkdir
    def synchronized(path,*args,**kwargs):
        if path==target:
            barrier.wait(timeout=5)
        return original(path,*args,**kwargs)
    monkeypatch.setattr(Path,'mkdir',synchronized)
    def restore(folder):
        try:
            return str(restore_backup(folder,target))
        except BackupError as error:
            return str(error)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(restore,[first,second]))
    assert results.count(str(target))==1
    assert results.count('restore_destination_exists')==1
    assert verify_backup(target).format=='sqlite-backup-v1'


def test_partial_restore_is_not_ready_and_app_refuses_to_start(client,application,tmp_path,monkeypatch):
    folder=create_backup(application.state.engine,RawStore(tmp_path/'raw'),tmp_path/'backups')
    target=tmp_path/'partial'
    original=__import__('os').link
    def fail_copy(source,destination,*args,**kwargs):
        if Path(destination)==target/'database.sqlite3':
            raise OSError('simulated copy failure')
        return original(source,destination,*args,**kwargs)
    monkeypatch.setattr('app.backup.os.link',fail_copy)
    with pytest.raises(OSError):
        restore_backup(folder,target)
    assert (target/'restore.pending').exists()
    with pytest.raises(BackupError,match='restore_incomplete'):
        verify_backup(target)
    with pytest.raises(RuntimeError,match='restore is incomplete'):
        with TestClient(create_app(Settings(database_url=f"sqlite:///{target/'database.sqlite3'}"))):
            pass
    assert not (target/'database.sqlite3').exists()
