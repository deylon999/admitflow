"""Execute the same write assertions against real PostgreSQL row locks."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from fastapi.testclient import TestClient
import pytest

from app.config import Settings
from app.main import create_app
from native_support import postgres_engine
from test_api import HEADERS, VALUES, create, start
from test_writes import (
    test_create_retry_returns_original_response_without_duplicates,
    test_snapshot_retry_does_not_extend_history_twice,
    test_delete_erases_cached_payload_and_does_not_resurrect_watch,
    test_idempotency_keys_are_scoped_to_owner,
    test_invalid_key_does_not_create_data,
    test_concurrent_retries_create_one_watch,
    test_concurrent_creation_cannot_exceed_watch_limit,
    test_concurrent_snapshots_cannot_exceed_history_limit,
)
from test_expected_snapshot import (
    test_stale_expected_snapshot_refuses_atomically_and_cached_replay_still_works,
    test_malformed_expected_snapshot_is_not_a_write,
)
from test_history_pages import test_all_500_with_equal_timestamps_and_new_insert, test_cursor_is_scoped_and_invalid_limits_rejected
from test_history_totals import test_history_total_is_all_records_not_page_size_and_is_owner_scoped
from test_history_versions import test_new_calculator_does_not_rewrite_saved_v1, test_unknown_history_version_refuses_instead_of_silent_recalculation

pytestmark = pytest.mark.postgres


@pytest.fixture
def application(postgres_engine):
    return create_app(Settings(
        database_url=postgres_engine.url.render_as_string(hide_password=False),
        auto_create_schema=False,
    ))


def test_two_application_pools_cannot_overwrite_same_expected_snapshot(client, application):
    start(client)
    watch = create(client)
    path = f"/api/v1/watches/{watch['id']}/snapshots"
    barrier = Barrier(2)
    second_app = create_app(Settings(
        database_url=application.state.engine.url.render_as_string(hide_password=False),
        auto_create_schema=False,
    ))
    with TestClient(second_app) as second:
        second.cookies.update(client.cookies)
        def send(index):
            barrier.wait(timeout=5)
            return (client if index == 0 else second).post(path, json=VALUES | {'rank': 121 + index}, headers=HEADERS | {
                'Idempotency-Key': f'parallel-expected-{index}',
                'X-Expected-Snapshot': watch['latest']['id'],
            })
        with ThreadPoolExecutor(max_workers=2) as pool:
            responses = list(pool.map(send, range(2)))
        assert sorted(r.status_code for r in responses) == [201, 409]
        winner = next(r for r in responses if r.status_code == 201)
        detail = client.get(f"/api/v1/watches/{watch['id']}").json()
        assert len(detail['history']) == 2
        assert detail['latest']['id'] == winner.json()['id']
