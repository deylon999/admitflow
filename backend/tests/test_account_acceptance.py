"""Final native-PG acceptance: populated guest graph and response privacy."""
from copy import deepcopy

from alembic import command
from fastapi.testclient import TestClient
from httpx import Cookies
import pytest
from sqlalchemy import inspect, select

from app.admissions import Assessment, ChangeEvent, Subscription
from app.config import Settings
from app.database import BrowserSession, LookupBudget, OperationRecord, Snapshot, Watch
from app.main import COOKIE, create_app
from app.sources.pilots import register_sgu
from app.sources.publishing import publish
from app.sources.storage import RawStore
from account_support import HEADERS, KEY, PASSWORD, RecordingMailer, auth_app, auth_client, csrf, postgres_engine, register  # noqa: F401
from test_account_login import login
from test_api import create
from test_changes import setup_change
from test_migrations import config as migration_config
from test_sgu_adapter import BINDING, KEY as SOURCE_KEY, response

pytestmark = pytest.mark.postgres


@pytest.fixture
def guest_graph(postgres_engine, monkeypatch, tmp_path):
    monkeypatch.setenv('SOURCE_IDENTITY_KEY', SOURCE_KEY.hex())
    mailer = RecordingMailer()
    app = create_app(Settings(database_url=postgres_engine.url.render_as_string(hide_password=False),
                              auto_create_schema=False, auth_enabled=True, auth_rate_key=KEY,
                              public_origin='http://testserver'), registration_mailer=mailer)
    app.state.registration_test_mailer = mailer
    with TestClient(app) as client:
        register_sgu(app.state.engine, enable=True, registry=app.state.source_registry)
        raw = response()
        parsed = app.state.source_registry.resolve(BINDING).parse(raw, BINDING)
        publish(app.state.engine, BINDING.source_id, parsed, raw, RawStore(tmp_path/'raw'), registry=app.state.source_registry)
        _, _, saved, _ = setup_change((client, app), tmp_path)
        watch = create(client)
        yield client, app, saved, watch


def rows(engine, tables):
    with engine.connect() as connection:
        return deepcopy({table.name: connection.execute(select(table).order_by(*table.primary_key.columns)).mappings().all() for table in tables})


def test_account_transitions_preserve_full_guest_graph_and_do_not_transfer_ownership(guest_graph):
    client, app, saved, watch = guest_graph
    tables = [model.__table__ for model in (BrowserSession, Watch, Snapshot, LookupBudget, OperationRecord, Subscription, Assessment, ChangeEvent)]
    before = rows(app.state.engine, tables)
    assert all(before[name] for name in before)
    guest_cookie = client.cookies.get(COOKIE)
    # Use the real single-use verification endpoint, never a direct DB confirmation.
    for email in ('first@example.org', 'second@example.org'):
        assert register(client, email=email).status_code == 202
        token = app.state.registration_test_mailer.deliveries[-1][1]
        assert client.post('/api/v1/auth/verification/confirm', json={'token': token}, headers=csrf(client)).status_code == 204
        assert login(client, email=email).status_code == 200
        assert client.cookies.get(COOKIE) == guest_cookie
        current = rows(app.state.engine, tables)
        current['browser_sessions'] = [row for row in current['browser_sessions'] if row['token_hash'] == before['browser_sessions'][0]['token_hash']]
        assert current == before
        with TestClient(app) as other:
            other.cookies = Cookies(client.cookies)
            other.cookies.delete(COOKIE, path='/api')
            assert other.get('/api/v1/auth/session').status_code == 200
            assert other.get('/api/v1/subscriptions').status_code == 401
            assert other.post('/api/v1/session', headers=HEADERS).status_code == 204
            assert other.get('/api/v1/subscriptions').json() == []
            assert other.get('/api/v1/changes').json()['items'] == []
            assert other.get(f"/api/v1/watches/{watch['id']}").status_code == 404
            assert other.get(f"/api/v1/subscriptions/{saved['id']}/history").status_code == 404
        # The other disposable guest is unrelated; compare only the original owner.
        assert client.post('/api/v1/auth/logout', json={}, headers=csrf(client)).status_code == 204
        assert client.cookies.get(COOKIE) == guest_cookie
        current = rows(app.state.engine, tables)
        current['browser_sessions'] = [row for row in current['browser_sessions'] if row['token_hash'] == before['browser_sessions'][0]['token_hash']]
        assert current == before


def test_additive_migration_preserves_populated_subscription_and_change_history(guest_graph):
    _, app, _, _ = guest_graph
    engine = app.state.engine
    cfg = migration_config()
    with engine.connect() as connection:
        cfg.attributes['connection'] = connection
        command.downgrade(cfg, '0011')  # Only the newly created disposable test schema.
        tables = [table for table in BrowserSession.metadata.sorted_tables if table.name in inspect(connection).get_table_names()]
    before = rows(engine, tables)
    assert before['subscriptions'] and before['assessments'] and before['change_events'] and before['snapshots']
    with engine.connect() as connection:
        cfg.attributes['connection'] = connection
        command.upgrade(cfg, 'head')
        command.check(cfg)
    assert rows(engine, tables) == before


def test_auth_responses_and_http_logs_are_noncacheable_and_secret_free(auth_client, auth_app, caplog):
    responses = [auth_client.get('/api/v1/auth/csrf', headers=HEADERS)]
    responses.append(register(auth_client))
    verification = auth_app.state.test_mailer.deliveries[-1][1]
    responses.append(auth_client.post('/api/v1/auth/verification/confirm', json={'token': verification}, headers=csrf(auth_client)))
    responses.append(login(auth_client))
    secrets = [PASSWORD, verification, *[cookie.value for cookie in auth_client.cookies.jar]]
    responses.append(auth_client.get('/api/v1/auth/session'))
    responses.append(auth_client.post('/api/v1/auth/refresh', json={}, headers=csrf(auth_client)))
    secrets.extend(cookie.value for cookie in auth_client.cookies.jar)
    responses.append(auth_client.post('/api/v1/auth/logout', json={}, headers=csrf(auth_client)))
    responses.append(auth_client.get('/api/v1/auth/session'))
    assert [item.status_code for item in responses] == [200, 202, 204, 200, 200, 200, 204, 401]
    for item in responses:
        assert item.headers['cache-control'] == 'no-store'
        assert item.headers['x-content-type-options'] == 'nosniff'
        assert all(secret not in item.text for secret in secrets)
    assert all(secret not in caplog.text for secret in secrets)
