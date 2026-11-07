"""The cron signal must name problems without any candidate data."""
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import pytest

spec=importlib.util.spec_from_file_location('ops_check',Path(__file__).parents[2]/'scripts/ops_check.py')
ops=importlib.util.module_from_spec(spec)
spec.loader.exec_module(ops)
HEALTHY=dict(worker=dict(state='alive'),sources=dict(byState=dict(archived=2)),jobs=dict(overdue=0))


def test_healthy_system_has_no_problems():
    assert ops.problems(HEALTHY,free_share=.5,backup_age_hours=1)==[]


def test_each_failure_is_named():
    broken=dict(worker=dict(state='stale'),sources=dict(byState=dict(quarantined=1,stale=1)),jobs=dict(overdue=2))
    assert ops.problems(broken,free_share=.1,backup_age_hours=30)==['worker_stale','sources_quarantined','sources_stale','jobs_overdue','disk_low','backup_old']
    assert ops.problems(HEALTHY,free_share=.5,backup_age_hours=None)==['backup_missing']
    assert ops.problems(None,free_share=.5,backup_age_hours=1)==['api_status_unavailable']


def test_only_verified_backups_count(tmp_path):
    (tmp_path/'unverified').mkdir()
    assert ops.newest_backup_hours(tmp_path) is None
    folder = tmp_path/'backup-0123456789abcdef0123456789abcdef'
    folder.mkdir()
    (folder/'restored-counts.txt').write_text('x')
    assert ops.newest_backup_hours(tmp_path) is None
    for name in ('db.dump', 'raw.tar'):
        (folder/name).write_bytes(b'fixture')
    (folder/'verified.json').write_text(json.dumps(dict(format='admitflow-postgres-backup-v1',id=folder.name,verifiedAt=datetime.now(timezone.utc).isoformat())))
    assert ops.newest_backup_hours(tmp_path)<1


@pytest.mark.parametrize('error', [FileNotFoundError(), subprocess.TimeoutExpired('docker', 60)])
def test_status_failure_is_reported(monkeypatch, error):
    def fail(*args, **kwargs):
        raise error
    monkeypatch.setattr(ops.subprocess, 'run', fail)
    assert ops.status('docker compose') is None
    assert ops.problems(None, free_share=.01, backup_age_hours=None) == ['api_status_unavailable', 'disk_low', 'backup_missing']


@pytest.mark.parametrize('body', ['not json', '{}', 'null', '{"worker": null}'])
def test_invalid_status_is_unavailable(monkeypatch, body):
    monkeypatch.setattr(ops.subprocess, 'run', lambda *a, **kw: subprocess.CompletedProcess([], 0, body))
    assert ops.status('docker compose') is None
