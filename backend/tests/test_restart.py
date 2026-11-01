"""Real local API process restarts on an isolated SQLite file, not PostgreSQL evidence."""
from contextlib import contextmanager
from datetime import timedelta
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

import httpx
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import Settings
from app.database import BrowserSession
from app.main import COOKIE, create_app, token_hash, utcnow
from test_api import HEADERS, VALUES, WATCH, create, start


@contextmanager
def running_api(database, port):
    environment = dict(os.environ, DATABASE_URL=f'sqlite:///{database.as_posix()}',
                       ENVIRONMENT='development', AUTO_CREATE_SCHEMA='true', SECURE_COOKIE='false',
                       ALLOWED_HOSTS='127.0.0.1', PUBLIC_ORIGIN='')
    process = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1',
                                '--port', str(port), '--no-access-log'], cwd=Path(__file__).resolve().parents[1],
                               env=environment, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        with httpx.Client(base_url=f'http://127.0.0.1:{port}', timeout=1, trust_env=False) as client:
            deadline = time.monotonic() + 15
            while True:
                if process.poll() is not None:
                    raise RuntimeError('Isolated API process exited before readiness')
                try:
                    if client.get('/api/ready').status_code == 200:
                        break
                except httpx.TransportError:
                    pass
                if time.monotonic() >= deadline:
                    raise RuntimeError('Isolated API readiness deadline exceeded')
                time.sleep(.05)
            yield client
    finally:
        if process.poll() is None:
            process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def test_process_restart_preserves_history_owner_deadline_and_operation_tombstones(tmp_path):
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        port = probe.getsockname()[1]
    database = tmp_path/'restart.db'
    create_headers = HEADERS|{'Idempotency-Key':'restart-create-001'}
    update_headers = HEADERS|{'Idempotency-Key':'restart-update-001'}
    values = VALUES|{'rank':121}
    with running_api(database, port) as first:
        start(first)
        token = first.cookies.get(COOKIE)
        expiry = first.get('/api/v1/session').json()
        response = first.post('/api/v1/watches', json=WATCH, headers=create_headers)
        assert response.status_code == 201
        created = response.json()
        response = first.post(f"/api/v1/watches/{created['id']}/snapshots", json=values, headers=update_headers)
        assert response.status_code == 201
        updated = response.json()
        original = first.get('/api/v1/export').json()['watches']
    with running_api(database, port) as second:
        assert second.get(f"/api/v1/watches/{created['id']}").status_code == 401
        second.cookies.set(COOKIE, token, domain='127.0.0.1', path='/api')
        assert second.get('/api/v1/session').json() == expiry
        assert second.get('/api/v1/export').json()['watches'] == original
        assert second.post('/api/v1/watches', json=WATCH, headers=create_headers).json() == created
        assert second.post(f"/api/v1/watches/{created['id']}/snapshots", json=values, headers=update_headers).json() == updated
        assert len(second.get(f"/api/v1/watches/{created['id']}").json()['history']) == 2
        second.cookies.clear()
        start(second)
        assert second.get(f"/api/v1/watches/{created['id']}").status_code == 404
        assert second.get('/api/v1/watches').json() == []
        second.cookies.clear()
        second.cookies.set(COOKIE, token, domain='127.0.0.1', path='/api')
        assert second.delete(f"/api/v1/watches/{created['id']}", headers=HEADERS).status_code == 204
    with running_api(database, port) as third:
        third.cookies.set(COOKIE, token, domain='127.0.0.1', path='/api')
        assert third.post('/api/v1/watches', json=WATCH, headers=create_headers).status_code == 410
        assert third.get('/api/v1/watches').json() == []


def test_lifespan_restart_does_not_reactivate_expired_owner(tmp_path):
    settings = Settings(database_url=f"sqlite:///{(tmp_path/'expired.db').as_posix()}")
    application = create_app(settings)
    with TestClient(application) as first:
        start(first)
        token = first.cookies.get(COOKIE)
        create(first)
        with Session(application.state.engine) as db:
            db.get(BrowserSession, token_hash(token)).expires_at = utcnow()-timedelta(seconds=1)
            db.commit()
    with TestClient(create_app(settings)) as second:
        second.cookies.set(COOKIE, token, domain='testserver.local', path='/api')
        assert second.get('/api/v1/watches').status_code == 401
        assert second.post('/api/v1/session', headers=HEADERS).status_code == 401
        assert second.delete('/api/v1/session', headers=HEADERS).status_code == 204
        start(second)
        assert second.cookies.get(COOKIE) != token
        assert second.get('/api/v1/watches').json() == []
