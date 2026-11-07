"""Backup safety: ownership, failed restores, missing raw objects and completion evidence."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tarfile
from types import SimpleNamespace

import pytest

spec = importlib.util.spec_from_file_location('production_backup', Path(__file__).parents[2] / 'scripts/backup_production.py')
backup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backup)


def archive(path, body=b'synthetic archive', *, name=None, link=False):
    reference = hashlib.sha256(body).hexdigest()
    with tarfile.open(path, 'w') as tar:
        member = tarfile.TarInfo(name or f'raw/{reference}')
        member.size = len(body)
        if link:
            member.type = tarfile.SYMTYPE
            member.linkname = '/etc/passwd'
        tar.addfile(member, io.BytesIO(body))
    return reference


def test_raw_archive_verifies_referenced_content_without_extracting(tmp_path):
    path = tmp_path / 'raw.tar'
    reference = archive(path)
    backup.verify_raw(path, [reference])
    assert list(tmp_path.iterdir()) == [path]
    with pytest.raises(ValueError, match='missing_or_invalid'):
        backup.verify_raw(path, ['0' * 64])
    archive(path, name=f'raw/{reference}', body=b'corrupt')
    with pytest.raises(ValueError, match='raw_hash_mismatch'):
        backup.verify_raw(path, [reference])
    archive(path, name=f'raw/{reference}', link=True)
    with pytest.raises(ValueError, match='missing_or_invalid'):
        backup.verify_raw(path, [reference])


def owned(root, number):
    folder = root / f'backup-{number:032x}'
    folder.mkdir()
    for name in backup.FILES:
        (folder / name).write_text('test')
    (folder / 'verified.json').write_text(json.dumps(dict(format=backup.FORMAT, id=folder.name, verifiedAt='2000-01-01T00:00:00+00:00')))
    return folder


def test_retention_preserves_unrelated_incomplete_and_modified_directories(tmp_path):
    good = owned(tmp_path, 1)
    unrelated = tmp_path / 'user-documents'
    unrelated.mkdir()
    (unrelated / 'important.txt').write_text('keep')
    incomplete = owned(tmp_path, 2)
    (incomplete / 'verified.json').unlink()
    modified = owned(tmp_path, 3)
    (modified / 'personal.txt').write_text('keep')
    backup.prune(tmp_path, 14)
    assert not good.exists()
    assert (unrelated / 'important.txt').read_text() == 'keep'
    assert incomplete.exists()
    assert (modified / 'personal.txt').read_text() == 'keep'


@pytest.mark.parametrize('failure', [None, 'createdb', 'pg_restore', 'raw'])
def test_completion_and_database_ownership(monkeypatch, tmp_path, failure):
    raw = tmp_path / 'fixture.tar'
    reference = archive(raw)
    calls = []

    def run(command, **kwargs):
        calls.append(command)
        operation = command[4]
        if operation == failure:
            raise subprocess.CalledProcessError(1, command)
        if operation == 'pg_dump':
            kwargs['stdout'].write(b'dump')
        elif operation == 'tar':
            kwargs['stdout'].write(raw.read_bytes())
        elif operation == 'psql':
            # Counts and references come from the restored dump, never the changing source.
            assert command[command.index('-d') + 1].startswith('admitflow_check_')
            payload = ('0' * 64 if failure == 'raw' else reference) if 'payload_hash' in command[-1] else 'watches|2'
            return subprocess.CompletedProcess(command, 0, (payload + '\n').encode())
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(backup.subprocess, 'run', run)
    output = tmp_path / 'backups'
    if failure:
        with pytest.raises((subprocess.CalledProcessError, ValueError)):
            backup.create_backup(output, ['docker'], 'worker', 14)
        assert not list(output.glob('backup-*'))
        assert not list(output.glob('*/verified.json'))
    else:
        folder, manifest = backup.create_backup(output, ['docker'], 'worker', 14)
        assert manifest['rawObjects'] == 1
        assert (folder / 'verified.json').is_file()
    drops = [command for command in calls if command[4] == 'dropdb']
    assert len(drops) == (0 if failure == 'createdb' else 1)
    assert all('--if-exists' not in command for command in calls)


def test_database_collision_never_drops_existing_database(monkeypatch, tmp_path):
    monkeypatch.setattr(backup, 'uuid4', lambda: SimpleNamespace(hex='1' * 32))
    calls = []
    def run(command, **kwargs):
        calls.append(command)
        if 'createdb' in command:
            raise subprocess.CalledProcessError(1, command)
    monkeypatch.setattr(backup.subprocess, 'run', run)
    with pytest.raises(subprocess.CalledProcessError):
        backup.create_backup(tmp_path, ['docker'], 'worker', 14)
    assert not any('dropdb' in command for command in calls)
