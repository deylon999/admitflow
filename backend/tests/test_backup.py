from datetime import timedelta
import json
import sqlite3

import pytest

from app.backup import BackupError, create_backup, file_hash
from app.sources.publishing import publish
from app.sources.storage import RawStore, StorageError
from source_helpers import NOW, parsed, raw, registry, seed_source
from test_api import create, start


def test_online_backup_includes_manual_history_and_all_raw_refs(client,application,tmp_path):
    start(client)
    watch=create(client)
    engine=application.state.engine
    seed_source(engine)
    store=RawStore(tmp_path/'raw')
    publish(engine,'source-1',parsed(),raw(),store,registry=registry(),allow_unattested=True)
    second=raw(b'new payload',NOW+timedelta(minutes=1))
    publish(engine,'source-1',parsed(),second,store,registry=registry(),allow_unattested=True)
    store.put(b'orphan not needed in backup')
    folder=create_backup(engine,store,tmp_path/'backups')
    manifest=json.loads((folder/'manifest.json').read_text())
    assert manifest['databaseHash']==file_hash(folder/'database.sqlite3')
    assert set(manifest['rawHashes'])=={raw().payload_hash,second.payload_hash}
    assert all((folder/'raw'/digest).exists() for digest in manifest['rawHashes'])
    with sqlite3.connect(folder/'database.sqlite3') as saved:
        assert saved.execute('SELECT id FROM watches').fetchone()[0]==watch['id']
        assert saved.execute('SELECT count(*) FROM source_snapshots').fetchone()[0]==2
        assert saved.execute('SELECT count(*) FROM candidate_entries').fetchone()[0]==6
    assert [path.name for path in (tmp_path/'backups').iterdir()]==[folder.name]


def test_missing_raw_aborts_without_ready_or_partial_backup(client,application,tmp_path):
    seed_source(application.state.engine)
    store=RawStore(tmp_path/'raw')
    publish(application.state.engine,'source-1',parsed(),raw(),store,registry=registry(),allow_unattested=True)
    (store.root/raw().payload_hash).unlink()
    with pytest.raises(StorageError):
        create_backup(application.state.engine,store,tmp_path/'backups')
    assert list((tmp_path/'backups').iterdir())==[]
    assert client.get('/api/live').status_code==200


def test_backup_timeout_leaves_no_completed_bundle(client,application,tmp_path):
    with pytest.raises(BackupError,match='backup_timeout'):
        create_backup(application.state.engine,RawStore(tmp_path/'raw'),tmp_path/'backups',timeout=-1)
    assert list((tmp_path/'backups').iterdir())==[]
