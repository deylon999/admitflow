"""A fresh Alembic process must see every persisted model on PostgreSQL."""
import os
from pathlib import Path
import subprocess
import sys

from native_support import postgres_engine  # noqa: F401


def test_standalone_alembic_check_keeps_worker_heartbeat_table(postgres_engine):
    result = subprocess.run(
        [sys.executable, '-m', 'alembic', 'check'],
        cwd=Path(__file__).resolve().parents[1],
        env={**os.environ, 'DATABASE_URL': postgres_engine.url.render_as_string(hide_password=False),
             'ENVIRONMENT': 'development', 'AUTO_CREATE_SCHEMA': 'false'},
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'No new upgrade operations detected' in result.stdout
