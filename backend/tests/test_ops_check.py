"""The cron signal must name problems without any candidate data."""
import importlib.util
from pathlib import Path

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
    (tmp_path/'good').mkdir()
    (tmp_path/'good'/'restored-counts.txt').write_text('x')
    assert ops.newest_backup_hours(tmp_path)<1
