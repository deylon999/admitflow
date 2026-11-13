from threading import Lock

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from native_support import postgres_engine  # noqa: F401

KEY = 'isolated-test-key-with-at-least-32-bytes'
PASSWORD = 'A sufficiently long passphrase!'
HEADERS = {'X-Requested-With': 'abiturient', 'Origin': 'http://testserver'}


class RecordingMailer:
    available = True

    def __init__(self):
        self.deliveries = []
        self.verification_deliveries = []
        self.recovery_deliveries = []
        self.lock = Lock()
        self.fail = False

    def deliver_registration(self, email, verification_token):
        if self.fail:
            raise RuntimeError('Synthetic provider failure with private details')
        with self.lock:
            self.deliveries.append((email, verification_token))


    def deliver_verification(self, email, verification_token):
        if self.fail: raise RuntimeError('Synthetic provider failure with private details')
        with self.lock: self.verification_deliveries.append((email, verification_token))

    def deliver_recovery(self, email, recovery_token):
        if self.fail: raise RuntimeError('Synthetic provider failure with private details')
        with self.lock: self.recovery_deliveries.append((email, recovery_token))


@pytest.fixture
def auth_app(postgres_engine):
    config = Settings(database_url=postgres_engine.url.render_as_string(hide_password=False),
                      auto_create_schema=False, auth_enabled=True, auth_rate_key=KEY,
                      public_origin='http://testserver')
    mailer = RecordingMailer()
    app = create_app(config, registration_mailer=mailer)
    app.state.test_mailer = mailer
    return app


@pytest.fixture
def auth_client(auth_app):
    with TestClient(auth_app, client=('192.0.2.1', 5000)) as client:
        yield client


def csrf(client):
    response = client.get('/api/v1/auth/csrf', headers=HEADERS)
    assert response.status_code == 200, response.text
    return HEADERS | {'X-CSRF-Token': response.json()['csrfToken']}


def register(client, email='person@example.org', password=PASSWORD, headers=None):
    return client.post('/api/v1/auth/register', json=dict(email=email, password=password),
                       headers=headers if headers is not None else csrf(client))
