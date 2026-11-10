"""Failure-path tests for the host launcher, not PostgreSQL acceptance evidence."""
import importlib.util
import json
from pathlib import Path
from unittest.mock import Mock

import pytest


@pytest.fixture
def launcher():
    path = Path(__file__).resolve().parents[2] / 'scripts/local_smoke.py'
    spec = importlib.util.spec_from_file_location('local_start', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_unavailable_docker_reports_failure_without_starting_or_using_sqlite(launcher, monkeypatch, tmp_path):
    monkeypatch.setattr('sys.argv', ['local_smoke.py', '--output', str(tmp_path)])
    monkeypatch.setattr(launcher, 'run', Mock(side_effect=RuntimeError('Docker unavailable')))
    compose = Mock()
    monkeypatch.setattr(launcher, 'compose', compose)
    assert launcher.main() == 1
    compose.assert_not_called()
    report = json.loads(next(tmp_path.glob('*.json')).read_text())
    assert report['success'] is False and report['error'] == 'Docker unavailable'
    assert not list(tmp_path.glob('*.dump'))


def test_backup_failure_prevents_backend_start_and_migrations(launcher, monkeypatch, tmp_path):
    config = {'services': {
        'db': {'environment': {'POSTGRES_USER': 'app', 'POSTGRES_DB': 'app'}},
        'backend': {'environment': {'DATABASE_URL': 'postgresql+psycopg://db/app', 'AUTO_CREATE_SCHEMA': 'false'}},
        'frontend': {'ports': [{'host_ip': '127.0.0.1', 'published': '8080'}]},
    }}
    calls = []

    def compose(*args, **kwargs):
        calls.append(args)
        if args[0] == 'config':
            return json.dumps(config).encode()
        if 'pg_dump' in args:
            raise RuntimeError('Backup failed')
        return b''

    monkeypatch.setattr('sys.argv', ['local_smoke.py', '--output', str(tmp_path)])
    monkeypatch.setattr(launcher, 'run', Mock(return_value=b'29'))
    monkeypatch.setattr(launcher, 'mounts', Mock(return_value=[('existing', '/data')]))
    monkeypatch.setattr(launcher, 'compose', compose)
    assert launcher.main() == 1
    assert not any('backend' in call for call in calls)
    report = json.loads(next(tmp_path.glob('*.json')).read_text())
    assert report['success'] is False and report['error'] == 'Backup failed'


def test_history_fingerprint_detects_changes_without_recording_private_rows(launcher, monkeypatch):
    rows = [b'private historical payload\n']

    def pg(sql, db):
        if sql.startswith('SELECT count'):
            return b'1\n'
        return rows[0]

    monkeypatch.setattr(launcher, 'pg', pg)
    columns = {'snapshots': ['id', 'rank']}
    _, before = launcher.history({}, columns)
    rows[0] = b'changed historical payload\n'
    _, after = launcher.history({}, columns)
    assert before != after
    assert before['snapshots']['rows'] == after['snapshots']['rows'] == 1
    assert 'private' not in json.dumps(before)


def test_launcher_propagates_failed_docker_command(launcher, monkeypatch):
    result = Mock(returncode=1, stderr=b'connection refused', stdout=b'')
    monkeypatch.setattr(launcher.subprocess, 'run', Mock(return_value=result))
    with pytest.raises(RuntimeError, match='connection refused'):
        launcher.run(['docker', 'info'])


def test_mounts_ignore_oneoff_maintenance_containers(launcher, monkeypatch):
    monkeypatch.setattr(launcher, 'compose', Mock(return_value=b'regular\noneoff\n'))
    def container(oneoff, name):
        return {'Config': {'Labels': {'com.docker.compose.oneoff': oneoff}},
                'Mounts': [{'Type': 'volume', 'Name': name, 'Destination': '/data'}]}
    monkeypatch.setattr(launcher, 'run', Mock(return_value=json.dumps([
        container('True', 'unrelated'), container('False', 'retained'),
    ]).encode()))
    assert launcher.mounts('backend') == [('retained', '/data')]
