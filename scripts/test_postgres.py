#!/usr/bin/env python3
"""Run mandatory native tests in an owned disposable Docker PostgreSQL instance."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
from postgres_runtime import disposable_postgres

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python', default=sys.executable, help='Python with backend development dependencies')
    parser.add_argument('tests', nargs='*', default=['tests/test_migrations.py'])
    args = parser.parse_args()
    with disposable_postgres() as runtime:
        env = {**os.environ, 'TEST_DATABASE_URL': runtime.url()}
        return subprocess.run([args.python, '-m', 'pytest', '-q', '--require-postgres', *args.tests],
                              cwd=ROOT / 'backend', env=env).returncode


if __name__ == '__main__':
    sys.exit(main())
