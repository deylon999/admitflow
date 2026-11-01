"""Local SQLite recovery tools. PostgreSQL backup/restore is a separate release gate."""
import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import time
from uuid import uuid4

from .config import Settings
from .database import make_engine
from .sources.storage import RawStore


class BackupError(Exception):
    pass


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


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    create=sub.add_parser('create')
    create.add_argument('--output',default='./var/backups')
    args=parser.parse_args(argv)
    engine=make_engine(Settings.from_env().database_url)
    try:
        result=create_backup(engine,RawStore(os.getenv('RAW_STORE_PATH','./var/raw')),args.output)
        print(json.dumps({'folder':str(result),'database':'sqlite','complete':True}))
        return 0
    except Exception:
        print(json.dumps({'error':'backup_failed','complete':False}))
        return 1
    finally:
        engine.dispose()


if __name__=='__main__':
    raise SystemExit(main())
