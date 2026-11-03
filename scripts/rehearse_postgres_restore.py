#!/usr/bin/env python3
"""Rehearse a quiesced synthetic PostgreSQL/raw restore; never opens a user DB."""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from dataclasses import replace
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


def rehearse(runtime, folder, *, archive_sgu=False):
    source_url, restored_url = runtime.url(), runtime.url('admitflow_test_restored')
    source = make_engine(source_url)
    restored = make_engine(restored_url)
    try:
        upgrade_schema(source)
        if archive_sgu:
            from test_sgu_adapter import BINDING,KEY,response as sgu_response
            from app.sources.pilots import register_sgu
            os.environ['SOURCE_IDENTITY_KEY']=KEY.hex()  # Synthetic fixture key; never printed.
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
        if archive_sgu:
            register_sgu(source,enable=True,registry=app.state.source_registry)
            response=sgu_response();adapter=app.state.source_registry.resolve(BINDING)
            publish(source,BINDING.source_id,adapter.parse(response,BINDING),response,store,registry=app.state.source_registry)
            with TestClient(app) as owner:
                owner.cookies.update(owner_cookies)
                def confirm(code):
                    found=owner.post(f'/api/v1/sources/{BINDING.source_id}/lookup',json={'publicCode':code},headers=HEADERS)
                    require(found.status_code==200,'Fixture lookup failed')
                    return {'confirmationToken':found.json()['confirmationToken']}
                from app.scenario_storage import enable_scenarios
                enable_scenarios(source,BINDING.source_id,registry=app.state.source_registry)
                archive_body=confirm('FIXTURE-000020')
                archive_saved=owner.post('/api/v1/subscriptions',json=archive_body,headers=HEADERS)
                require(archive_saved.status_code==201,'Archive save failed')
                archive_path=f"/api/v1/subscriptions/{archive_saved.json()['id']}"
                retired_body=confirm('FIXTURE-000002')
                retired=owner.post('/api/v1/subscriptions',json=retired_body,headers=HEADERS)
                require(retired.status_code==201,'Archive tombstone setup failed')
                require(owner.delete('/api/v1/subscriptions/'+retired.json()['id'],headers=HEADERS).status_code==204,'Archive delete failed')
                from test_scenario_storage import changed_consent
                changed,response=changed_consent(app,folder)
                publish(source,BINDING.source_id,changed,response,store,registry=app.state.source_registry)
                archive_scenarios=owner.get(archive_path+'/scenario-history').json()
                require(archive_scenarios['total']==2,'Scenario history setup differs')
                changes=owner.get('/api/v1/changes').json()
                require(changes['total']==1 and changes['unreadCount']==1,'Change event setup differs')
                event_id=changes['items'][0]['id']
                require(owner.post('/api/v1/changes/'+event_id+'/seen',headers=HEADERS).status_code==200,'Seen setup failed')
                seen_changes=owner.get('/api/v1/changes').json()
                archive_history=owner.get(archive_path+'/history').json()
                require(archive_history['total']==2,'Archive history setup differs')
                archive_facts=owner.get('/api/v1/subscriptions').json()
        else:
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
            if archive_sgu:
                require(owner.get('/api/v1/subscriptions').json()==archive_facts,'Restored archive facts differ')
                require(owner.get(archive_path+'/history').json()==archive_history,'Restored archive history differs')
                require(owner.get(archive_path+'/scenario-history').json()==archive_scenarios,'Restored scenario versions differ')
                require(owner.get('/api/v1/changes').json()==seen_changes,'Restored change/seen state differs')
                require(other.get('/api/v1/changes').json()['total']==0,'Restored events leaked')
                require(other.get(archive_path+'/history').status_code==404,'Restored archive ownership failed')
                require(other.get('/api/v1/subscriptions').json()==[],'Restored archive owner leaked')
                retry=owner.post('/api/v1/subscriptions',json=archive_body,headers=HEADERS)
                require(retry.status_code==201 and retry.json()==archive_saved.json(),'Restored archive confirmation replay differs')
                require(owner.post('/api/v1/subscriptions',json=retired_body,headers=HEADERS).status_code==410,'Restored archive tombstone resurrected')
                found=owner.post(f'/api/v1/sources/{BINDING.source_id}/lookup',json={'publicCode':'FIXTURE-000001'},headers=HEADERS)
                require(found.status_code==200 and found.json()['found'],'Restored identity key/source lookup differs')
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
                    archiveFacts=archive_sgu,archiveHistory=archive_sgu,identityKeyContinuity=archive_sgu,scenarioVersions=archive_sgu,changeSeenState=archive_sgu,
                    rpo='0 writes during quiesced rehearsal only; production RPO not measured')
    finally:
        source.dispose()
        restored.dispose()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--archive-sgu',action='store_true',help='Use anonymized real SGU DOM, never fetch external websites')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='admitflow-restore-') as folder:
        with disposable_postgres() as runtime:
            report = rehearse(runtime, Path(folder),archive_sgu=args.archive_sgu)
    report.update(recordedAt=datetime.now(timezone.utc).isoformat(), cleanup=True,
                  scope=('anonymized SGU573-row archive+synthetic consent change/scenarios/events/seen' if args.archive_sgu else 'synthetic')+';disposable PostgreSQL17/quiesced rehearsal,no production backup guarantee')
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
