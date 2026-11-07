"""Verify owned PostgreSQL/raw backups without touching other directories or databases."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import tarfile
import time
from uuid import uuid4

FORMAT = 'admitflow-postgres-backup-v1'
FILES = {'db.dump', 'raw.tar', 'restored-counts.txt', 'verified.json'}
NAME = re.compile(r'backup-[0-9a-f]{32}')
COUNTS = "SELECT table_name, (xpath($$/row/c/text()$$, query_to_xml(format($$SELECT count(*) AS c FROM %I$$, table_name), false, true, $$$$)))[1]::text FROM information_schema.tables WHERE table_schema = $$public$$ AND table_type = 'BASE TABLE' ORDER BY 1"


def digest(file):
    result = hashlib.sha256()
    for chunk in iter(lambda: file.read(1024 * 1024), b''):
        result.update(chunk)
    return result.hexdigest()


def verify_raw(archive, references):
    with tarfile.open(archive) as tar:
        members = {}
        for member in tar:
            if member.name in members:
                raise ValueError('duplicate_raw_member')
            members[member.name] = member
        for reference in references:
            if not re.fullmatch(r'[0-9a-f]{64}', reference):
                raise ValueError('invalid_raw_reference')
            member = members.get(f'raw/{reference}')
            if member is None or not member.isfile() or member.size > 8 * 1024 * 1024:
                raise ValueError('missing_or_invalid_raw_object')
            with tar.extractfile(member) as file:
                if digest(file) != reference:
                    raise ValueError('raw_hash_mismatch')


def prune(root, keep_days, *, now=None):
    cutoff = (time.time() if now is None else now) - keep_days * 86400
    for folder in root.iterdir():
        if not NAME.fullmatch(folder.name) or folder.is_symlink() or not folder.is_dir():
            continue
        children = list(folder.iterdir())
        if {child.name for child in children} != FILES or any(child.is_symlink() or not child.is_file() for child in children):
            continue
        try:
            manifest = json.loads((folder / 'verified.json').read_text(encoding='utf-8'))
            completed = datetime.fromisoformat(manifest['verifiedAt']).timestamp()
        except (ValueError, KeyError, TypeError):
            continue
        if manifest.get('format') != FORMAT or manifest.get('id') != folder.name or completed >= cutoff:
            continue
        # No recursive deletion: an unexpected file or directory must survive.
        for child in children:
            child.unlink()
        folder.rmdir()


def create_backup(output, compose, raw_service, keep_days):
    if not 1 <= keep_days <= 36500:
        raise ValueError('KEEP_DAYS must be between 1 and 36500')
    os.umask(0o077)
    root = Path(output).resolve()
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    identifier = uuid4().hex
    folder = root / f'.writing-{identifier}'
    folder.mkdir(mode=0o700)
    check = f'admitflow_check_{identifier}'
    created = False

    def run(service, *args, **kwargs):
        return subprocess.run([*compose, 'exec', '-T', service, *args], check=True, timeout=600, **kwargs)

    def sql(query):
        return run('db', 'psql', '-X', '-qAt', '-v', 'ON_ERROR_STOP=1', '-U', 'admitflow', '-d', check,
                   '-c', query, capture_output=True).stdout.decode('utf-8')

    try:
        with (folder / 'db.dump').open('xb') as file:
            run('db', 'pg_dump', '-Fc', '-U', 'admitflow', 'admitflow', stdout=file)
        with (folder / 'raw.tar').open('xb') as file:
            run(raw_service, 'tar', '-C', '/app/var', '-cf', '-', 'raw', stdout=file)
        # createdb must succeed before this run owns the name; never drop on collision.
        run('db', 'createdb', '-U', 'admitflow', check)
        created = True
        with (folder / 'db.dump').open('rb') as file:
            run('db', 'pg_restore', '--exit-on-error', '--no-owner', '-U', 'admitflow', '-d', check, stdin=file)
        counts = sql(COUNTS)
        (folder / 'restored-counts.txt').write_text(counts, encoding='utf-8')
        references = sql('SELECT DISTINCT payload_hash FROM source_snapshots ORDER BY payload_hash').splitlines()
        verify_raw(folder / 'raw.tar', references)
        with (folder / 'db.dump').open('rb') as file:
            database_hash = digest(file)
    finally:
        if created:
            run('db', 'dropdb', '-U', 'admitflow', check)
    # Publish success only after restoration, raw verification and cleanup.
    final = root / f'backup-{identifier}'
    manifest = dict(format=FORMAT, id=final.name, verifiedAt=datetime.now(timezone.utc).isoformat(),
                    databaseHash=database_hash, rawObjects=len(references), tables=len(counts.splitlines()))
    (folder / 'verified.json').write_text(json.dumps(manifest) + '\n', encoding='utf-8')
    folder.rename(final)
    prune(root, keep_days)
    return final, manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output')
    args = parser.parse_args()
    final, manifest = create_backup(args.output, shlex.split(os.getenv('COMPOSE', 'docker compose -f compose.prod.yaml')),
                                    os.getenv('RAW_SERVICE', 'worker'), int(os.getenv('KEEP_DAYS', '14')))
    print(json.dumps(dict(backup=str(final), verified=True, tables=manifest['tables'])))


if __name__ == '__main__':
    main()
