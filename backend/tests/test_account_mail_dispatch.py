"""Native PostgreSQL contract tests; recording transport is not live SMTP evidence."""
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
import pytest
from app.account_limits import AuthRateExceeded, consume_mail_cooldown
from app.accounts import AccountRateBucket, AccountUser
from account_support import auth_app, auth_client, csrf, postgres_engine, register, KEY
from test_account_email_verification import request_verification, confirm
from test_account_recovery import request_recovery

pytestmark = pytest.mark.postgres


def test_dispatch_means_real_transport_call_not_202_or_account_eligibility(auth_client, auth_app):
    first = register(auth_client)
    duplicate = register(auth_client)
    assert first.json() == duplicate.json()
    assert first.json()['dispatch'] == 'accepted'
    assert len(auth_app.state.test_mailer.deliveries) == 2
    assert auth_app.state.test_mailer.deliveries[-1][1] is None
    # Third notice is submitted, fourth is suppressed without a transport call.
    assert register(auth_client).json()['dispatch'] == 'accepted'
    suppressed = register(auth_client)
    assert suppressed.status_code == 202
    assert suppressed.json()['dispatch'] == 'suppressed'
    assert suppressed.json()['retryAfterSeconds'] == 3600
    assert len(auth_app.state.test_mailer.deliveries) == 3


@pytest.mark.parametrize('state', ['missing', 'unverified', 'verified', 'disabled'])
@pytest.mark.parametrize('operation', ['verify', 'recover'])
def test_dispatch_uniform_for_all_account_states(auth_client, auth_app, state, operation):
    if state != 'missing':
        register(auth_client)
        with Session(auth_app.state.engine) as db:
            user = db.scalar(select(AccountUser))
            if state == 'verified': user.email_verified_at = datetime.now(timezone.utc)
            if state == 'disabled': user.status = 'disabled'
            db.commit()
    request = request_verification if operation == 'verify' else request_recovery
    result = request(auth_client)
    assert result.status_code == 202
    assert result.json()['dispatch'] == 'accepted'
    auth_app.state.test_mailer.fail = True
    # Different address avoids the cooldown; identical failure before/after lookup.
    failure = request(auth_client, email='another@example.org')
    assert failure.status_code == 503 and 'dispatch' not in failure.json()


def test_rolling_cooldown_across_window_boundary_and_database_connections(postgres_engine):
    start = datetime(2026, 11, 14, 12, 0, 59, tzinfo=timezone.utc)
    consume_mail_cooldown(postgres_engine, KEY, 'person@example.org', now=start)
    with pytest.raises(AuthRateExceeded) as error:
        consume_mail_cooldown(postgres_engine, KEY, 'person@example.org', now=start+timedelta(seconds=2))
    assert error.value.retry_after == 58
    consume_mail_cooldown(postgres_engine, KEY, 'person@example.org', now=start+timedelta(seconds=60))
    with Session(postgres_engine) as db:
        row = db.scalar(select(AccountRateBucket))
        assert 'person' not in row.subject_hash and row.used == 1


def test_resend_cooldown_never_retires_previous_link(auth_client, auth_app):
    register(auth_client)
    first = request_verification(auth_client)
    token = auth_app.state.test_mailer.verification_deliveries[-1][1]
    second = request_verification(auth_client)
    assert first.json()['dispatch'] == 'accepted'
    assert second.status_code == 429 and 1 <= int(second.headers['retry-after']) <= 60
    assert len(auth_app.state.test_mailer.verification_deliveries) == 1
    assert confirm(auth_client, token).status_code == 204
