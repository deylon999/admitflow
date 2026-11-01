"""Local SQLite recovery tools. PostgreSQL backup/restore is a separate release gate."""
import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import time
from typing import Annotated, Literal
from uuid import uuid4

from pydantic import AwareDatetime, Field

from .config import Settings
from .calculation import CamelModel
from .database import make_engine
from .sources.storage import RawStore


class BackupError(Exception):
    pass


class BackupManifest(CamelModel):
    format: Literal['sqlite-backup-v1']
    created_at: AwareDatetime
    schema_revision: str | None = Field(max_length=80)
    database_hash: str = Field(pattern='^[a-f0-9]{64}$')
    raw_hashes: list[Annotated[str,Field(pattern='^[a-f0-9]{64}$')]] = Field(max_length=100_000)


def file_hash(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as file:
        for chunk in iter(lambda:file.read(65536),b''):
            digest.update(chunk)
    return digest.hexdigest()


def raw_references(db):
    exists=db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='source_snapshots'").fetchone()
    return sorted({row[0] for row in db.execute('SELECT payload_hash FROM source_snapshots')}) if exists else []


def write_private(path,body):
    with os.fdopen(os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as file:
        file.write(body)
        file.flush()
        os.fsync(file.fileno())


def remove_staging(folder,root):
    if folder.resolve().parent!=root.resolve() or not folder.name.startswith('.writing-'):
        raise BackupError('unsafe_staging_path')
    raw=folder/'raw'
    if raw.exists():
        for path in raw.iterdir():
            if path.is_file() or path.is_symlink():
                path.unlink()
        raw.rmdir()
    for name in ('database.sqlite3','database.sqlite3-journal','database.sqlite3-wal','database.sqlite3-shm','manifest.json'):
        (folder/name).unlink(missing_ok=True)
    folder.rmdir()


def create_backup(engine,store,output,*,timeout=60):
    if engine.dialect.name!='sqlite' or engine.url.database in (None,'',':memory:'):
        raise BackupError('requires_file_sqlite')
    root=Path(output).resolve()
    root.mkdir(parents=True,exist_ok=True,mode=0o700)
    folder=root/f'backup-{uuid4()}'
    staging=root/f'.writing-{uuid4()}'
    staging.mkdir(mode=0o700)
    database=staging/'database.sqlite3'
    deadline=time.monotonic()+timeout
    def progress(*_):
        if time.monotonic()>deadline:
            raise BackupError('backup_timeout')
    try:
        with store.locked():
            write_private(database,b'')
            with closing(engine.raw_connection()) as source, closing(sqlite3.connect(database)) as target:
                source.driver_connection.backup(target,pages=100,progress=progress,sleep=0.01)
                if target.execute('PRAGMA integrity_check').fetchall()!=[('ok',)]:
                    raise BackupError('backup_integrity_failed')
                if target.execute('PRAGMA foreign_key_check').fetchone():
                    raise BackupError('backup_foreign_key_failed')
                references=raw_references(target)
                has_revision=target.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='alembic_version'").fetchone()
                revision=target.execute('SELECT version_num FROM alembic_version').fetchone()[0] if has_revision else None
            saved=RawStore(staging/'raw',max_bytes=store.max_bytes)
            for digest in references:
                progress()
                saved.put(store.read(digest),digest)
            manifest=dict(format='sqlite-backup-v1',createdAt=datetime.now(timezone.utc).isoformat(),schemaRevision=revision,databaseHash=file_hash(database),rawHashes=references)
            write_private(staging/'manifest.json',json.dumps(manifest,sort_keys=True).encode())
            staging.rename(folder)
        return folder
    finally:
        if staging.exists():
            remove_staging(staging,root)


def verify_backup(folder):
    folder=Path(folder).resolve()
    database=folder/'database.sqlite3'
    manifest_path=folder/'manifest.json'
    if any(path.is_symlink() for path in (database,manifest_path,folder/'raw')):
        raise BackupError('unsafe_backup_path')
    if not database.is_file() or not manifest_path.is_file() or not (folder/'raw').is_dir():
        raise BackupError('incomplete_backup')
    with manifest_path.open('rb') as file:
        payload=file.read(8*1024*1024+1)
    if len(payload)>8*1024*1024:
        raise BackupError('invalid_backup_manifest')
    manifest=BackupManifest.model_validate_json(payload)
    if len(manifest.raw_hashes)!=len(set(manifest.raw_hashes)) or file_hash(database)!=manifest.database_hash:
        raise BackupError('backup_hash_mismatch')
    with closing(sqlite3.connect(database.as_uri()+'?mode=ro',uri=True)) as db:
        db.execute('PRAGMA trusted_schema=OFF')
        if db.execute('PRAGMA integrity_check').fetchall()!=[('ok',)] or db.execute('PRAGMA foreign_key_check').fetchone():
            raise BackupError('backup_integrity_failed')
        if db.execute("SELECT 1 FROM sqlite_master WHERE type IN ('trigger','view') LIMIT 1").fetchone():
            raise BackupError('unexpected_backup_schema')
        tables={row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {'browser_sessions','watches','snapshots','sources','source_snapshots','alembic_version'}<=tables:
            raise BackupError('unsupported_backup_schema')
        if db.execute('SELECT version_num FROM alembic_version').fetchone()[0]!=manifest.schema_revision:
            raise BackupError('backup_revision_mismatch')
        if raw_references(db)!=sorted(manifest.raw_hashes):
            raise BackupError('backup_references_mismatch')
    store=RawStore(folder/'raw')
    with store.locked():
        for digest in manifest.raw_hashes:
            store.read(digest)
    return manifest


def restore_backup(folder,destination):
    folder=Path(folder).resolve()
    if (folder/'raw').is_symlink() or not (folder/'raw').is_dir():
        raise BackupError('unsafe_backup_path')
    requested=Path(destination).absolute()
    if requested.exists() or requested.is_symlink():
        raise BackupError('restore_destination_exists')
    root=requested.parent.resolve()
    target=root/requested.name
    if target.is_relative_to(folder):
        raise BackupError('restore_inside_backup_forbidden')
    root.mkdir(parents=True,exist_ok=True,mode=0o700)
    staging=root/f'.writing-{uuid4()}'
    staging.mkdir(mode=0o700)
    try:
        saved=RawStore(folder/'raw')
        with saved.locked():
            manifest=verify_backup(folder)
            with (folder/'database.sqlite3').open('rb') as source, os.fdopen(os.open(staging/'database.sqlite3',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as output:
                shutil.copyfileobj(source,output,65536)
                output.flush()
                os.fsync(output.fileno())
            restored=RawStore(staging/'raw')
            for digest in manifest.raw_hashes:
                restored.put(saved.read(digest),digest)
            write_private(staging/'manifest.json',manifest.model_dump_json(by_alias=True).encode())
            verify_backup(staging)
            # Another restore cannot overwrite a populated destination.
            if target.exists() or target.is_symlink():
                raise BackupError('restore_destination_exists')
            staging.rename(target)
        return target
    finally:
        if staging.exists():
            remove_staging(staging,root)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    create=sub.add_parser('create')
    create.add_argument('--output',default='./var/backups')
    restore=sub.add_parser('restore')
    restore.add_argument('folder')
    restore.add_argument('--destination',required=True)
    verify=sub.add_parser('verify')
    verify.add_argument('folder')
    args=parser.parse_args(argv)
    engine=None
    try:
        if args.command=='create':
            engine=make_engine(Settings.from_env().database_url)
            result=create_backup(engine,RawStore(os.getenv('RAW_STORE_PATH','./var/raw')),args.output)
            print(json.dumps({'folder':str(result),'database':'sqlite','complete':True}))
        elif args.command=='restore':
            result=restore_backup(args.folder,args.destination)
            print(json.dumps({'folder':str(result),'database':'sqlite','complete':True}))
        else:
            manifest=verify_backup(args.folder)
            print(json.dumps({'valid':True,'schemaRevision':manifest.schema_revision,'rawCount':len(manifest.raw_hashes)}))
        return 0
    except Exception:
        print(json.dumps({'error':'backup_failed','complete':False}))
        return 1
    finally:
        if engine is not None:
            engine.dispose()


if __name__=='__main__':
    raise SystemExit(main())
