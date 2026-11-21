"""Owned disposable Docker PostgreSQL runtime for local verification only."""
from contextlib import contextmanager
from dataclasses import dataclass
import json
import subprocess
import time
from uuid import uuid4


@dataclass(frozen=True)
class PostgresRuntime:
    name: str
    port: str

    def url(self, database='admitflow_test_native'):
        return f'postgresql+psycopg://admitflow:admitflow@127.0.0.1:{self.port}/{database}'

    def command(self, *args, **kwargs):
        return subprocess.run(['docker', 'exec', '-i', self.name, *args], **kwargs)


@contextmanager
def disposable_postgres():
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
            # initdb's temporary Unix-socket server is not sufficient.
            ready = subprocess.run(['docker', 'exec', name, 'pg_isready', '-h', '127.0.0.1', '-U', 'admitflow'],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if ready.returncode == 0:
                break
            if time.monotonic() >= deadline:
                raise RuntimeError('Disposable PostgreSQL did not become ready within 60 seconds')
            time.sleep(0.25)
        ports = json.loads(subprocess.check_output(['docker', 'inspect', '--format', '{{json .NetworkSettings.Ports}}', name]))
        yield PostgresRuntime(name, ports['5432/tcp'][0]['HostPort'])
    finally:
        if created:
            subprocess.run(['docker', 'stop', '--time', '5', name], check=True, stdout=subprocess.DEVNULL)
