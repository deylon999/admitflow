#!/usr/bin/env python3
"""Rehearse a quiesced synthetic PostgreSQL/raw restore; never opens a user DB."""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import time

from postgres_runtime import disposable_postgres

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'backend'), str(ROOT / 'backend/tests')]

from fastapi.testclient import TestClient
from sqlalchemy import inspect, select, text

from app.admissions import SourceSnapshot
from app.config import Settings
from app.database import make_engine
from app.jobs import enqueue
from app.main import create_app
from app.migrations import upgrade_schema
from app.sources.publishing import publish
from app.sources.storage import RawStore, StorageError
from source_helpers import NOW, parsed, raw, registry, seed_source
from test_api import HEADERS, VALUES, WATCH


def require(value, message):
    if not value:
        raise RuntimeError(message)


def inventory(engine):
    with engine.connect() as db:
        return {name: sorted(repr(tuple(row)) for row in db.execute(text(f'SELECT * FROM "{name}"')))
                for name in inspect(engine).get_table_names()}


def rehearse(runtime, folder):
    source_url, restored_url = runtime.url(), runtime.url('admitflow_test_restored')
    source = make_engine(source_url)
    restored = make_engine(restored_url)
    try:
        upgrade_schema(source)
        store = RawStore(folder / 'source-raw')
        app = create_app(Settings(database_url=source_url, auto_create_schema=False))
        with TestClient(app) as owner, TestClient(app) as other:
            require(owner.post('/api/v1/session', headers=HEADERS).status_code == 204, 'Owner bootstrap failed')
            require(other.post('/api/v1/session', headers=HEADERS).status_code == 204, 'Other bootstrap failed')
            create_headers = HEADERS | {'Idempotency-Key': 'restore-create-001'}
            created = owner.post('/api/v1/watches', json=WATCH, headers=create_headers)
            require(created.status_code == 201, 'Create failed')
            watch = created.json()
            path = f"/api/v1/watches/{watch['id']}"
            update_headers = HEADERS | {'Idempotency-Key': 'restore-update-001'}
            updated = owner.post(path + '/snapshots', json=VALUES | {'rank': 121}, headers=update_headers)
            require(updated.status_code == 201, 'Update failed')
            removed = owner.post('/api/v1/watches', json=WATCH, headers=HEADERS | {'Idempotency-Key': 'restore-deleted-001'})
            require(removed.status_code == 201, 'Tombstone preparation failed')
            require(owner.delete('/api/v1/watches/' + removed.json()['id'], headers=HEADERS).status_code == 204, 'Delete failed')
            detail = owner.get(path).json()
            deadline = owner.get('/api/v1/session').json()
            owner_cookies, other_cookies = dict(owner.cookies), dict(other.cookies)
        seed_source(source)
        for response in (raw(), raw(b'second synthetic raw payload', NOW + timedelta(minutes=1))):
            publish(source, 'source-1', parsed(), response, store, registry=registry(), allow_unattested=True)
        enqueue(source, 'source-1', now=NOW)
        store.put(b'orphan excluded from the referenced backup')
        before = inventory(source)
        backup_start = time.monotonic()
        # All writers are quiesced. Keep raw publication/retention excluded throughout dump+copy.
        with store.locked():
            dump = runtime.command('pg_dump', '-U', 'admitflow', '-d', 'admitflow_test_native', '-Fc',
                                   check=True, capture_output=True).stdout
            with source.connect() as db:
                hashes = sorted(set(db.scalars(select(SourceSnapshot.payload_hash))))
            saved_raw = {digest: store.read(digest) for digest in hashes}
        backup_seconds = time.monotonic() - backup_start
        (folder / 'database.dump').write_bytes(dump)
        runtime.command('createdb', '-U', 'admitflow', 'admitflow_test_corrupt', check=True, capture_output=True)
        bad = runtime.command('pg_restore', '-U', 'admitflow', '-d', 'admitflow_test_corrupt',
                              '--single-transaction', '--exit-on-error', '--no-owner', input=dump[:len(dump)//2], capture_output=True)
        require(bad.returncode != 0, 'Truncated archive was accepted')
        corrupt = make_engine(runtime.url('admitflow_test_corrupt'))
        try:
            require(inspect(corrupt).get_table_names() == [], 'Failed restore left partial tables')
        finally:
            corrupt.dispose()
        restore_start = time.monotonic()
        runtime.command('createdb', '-U', 'admitflow', 'admitflow_test_restored', check=True, capture_output=True)
        runtime.command('pg_restore', '-U', 'admitflow', '-d', 'admitflow_test_restored',
                        '--single-transaction', '--exit-on-error', '--no-owner', input=dump, check=True, capture_output=True)
        restored_store = RawStore(folder / 'restored-raw')
        for digest, body in saved_raw.items():
            restored_store.put(body, digest)
        require(inventory(restored) == before, 'Restored table contents differ')
        restored_app = create_app(Settings(database_url=restored_url, auto_create_schema=False))
        with TestClient(restored_app) as owner, TestClient(restored_app) as other:
            owner.cookies.update(owner_cookies)
            other.cookies.update(other_cookies)
            require(owner.get(path).json() == detail, 'Manual history differs')
            require(owner.get('/api/v1/session').json() == deadline, 'Owner deadline/scope differs')
            require(other.get(path).status_code == 404, 'Ownership isolation failed')
            require(other.get('/api/v1/watches').json() == [], 'Foreign owner sees data')
            retry = owner.post('/api/v1/watches', json=WATCH, headers=create_headers)
            require(retry.status_code == 201 and retry.json() == watch, 'Create replay differs')
            retry = owner.post(path + '/snapshots', json=VALUES | {'rank': 121}, headers=update_headers)
            require(retry.status_code == 201 and retry.json() == updated.json(), 'Update replay differs')
            require(owner.post('/api/v1/watches', json=WATCH, headers=HEADERS | {'Idempotency-Key': 'restore-deleted-001'}).status_code == 410, 'Tombstone resurrected data')
            require(owner.get(path).json() == detail, 'Retries changed history')
        for digest, body in saved_raw.items():
            require(restored_store.read(digest) == body, 'Raw bytes differ')
        restore_seconds = time.monotonic() - restore_start
        digest = hashes[0]
        (restored_store.root / digest).write_bytes(b'corrupt raw')
        try:
            restored_store.read(digest)
        except StorageError as error:
            require(error.code == 'raw_hash_mismatch', 'Unexpected corruption refusal')
        else:
            raise RuntimeError('Corrupt raw was accepted')
        return dict(success=True, tables=len(before), counts={name: len(rows) for name, rows in before.items()},
                    referencedRawFiles=len(hashes), dumpBytes=len(dump), dumpSha256=hashlib.sha256(dump).hexdigest(),
                    backupSeconds=round(backup_seconds, 3), restoreAndValidationSeconds=round(restore_seconds, 3),
                    corruptionChecks=['truncated archive rolls back all tables', 'raw SHA256 mismatch refused'],
                    ownership=True, exactHistory=True, exactTableContents=True, retryAndTombstone=True,
                    rpo='0 writes during quiesced rehearsal only; production RPO not measured')
    finally:
        source.dispose()
        restored.dispose()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='admitflow-restore-') as folder:
        with disposable_postgres() as runtime:
            report = rehearse(runtime, Path(folder))
    report.update(recordedAt=datetime.now(timezone.utc).isoformat(), cleanup=True,
                  scope='disposable PostgreSQL17 synthetic/quiesced rehearsal, no production backup guarantee')
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
