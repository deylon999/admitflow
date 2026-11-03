#!/usr/bin/env python3
"""Run mandatory native tests in an owned disposable Docker PostgreSQL instance."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python', default=sys.executable, help='Python with backend development dependencies')
    parser.add_argument('tests', nargs='*', default=['tests/test_migrations.py'])
    args = parser.parse_args()
    name = f'admitflow-test-{uuid4().hex}'
    created = False
    try:
        subprocess.run([
            'docker', 'run', '--detach', '--rm', '--name', name,
            '--publish', '127.0.0.1::5432',
            '--env', 'POSTGRES_USER=admitflow', '--env', 'POSTGRES_PASSWORD=admitflow',
            '--env', 'POSTGRES_DB=admitflow_test_native', 'postgres:17-alpine',
        ], check=True, stdout=subprocess.DEVNULL)
        created = True
        deadline = time.monotonic() + 60
        while True:
            ready = subprocess.run(['docker', 'exec', name, 'pg_isready', '-U', 'admitflow'],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # initdb starts a temporary Unix-socket-only server; require TCP readiness.
            if ready.returncode == 0:
                ready = subprocess.run(['docker', 'exec', name, 'pg_isready', '-h', '127.0.0.1', '-U', 'admitflow'],
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if ready.returncode == 0:
                    break
            if time.monotonic() >= deadline:
                raise RuntimeError('Disposable PostgreSQL did not become ready within 60 seconds')
            time.sleep(0.25)
        ports = json.loads(subprocess.check_output(['docker', 'inspect', '--format', '{{json .NetworkSettings.Ports}}', name]))
        port = ports['5432/tcp'][0]['HostPort']
        env = {**os.environ, 'TEST_DATABASE_URL': f'postgresql+psycopg://admitflow:admitflow@127.0.0.1:{port}/admitflow_test_native'}
        return subprocess.run([args.python, '-m', 'pytest', '-q', '--require-postgres', *args.tests],
                              cwd=ROOT / 'backend', env=env).returncode
    finally:
        if created:
            subprocess.run(['docker', 'stop', '--time', '5', name], check=True, stdout=subprocess.DEVNULL)


if __name__ == '__main__':
    sys.exit(main())
