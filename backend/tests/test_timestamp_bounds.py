import pytest
from pydantic import ValidationError
from app.schemas import SessionRead
from test_api import start, create, HEADERS


@pytest.mark.parametrize('value', ['0001-01-01T00:00:00+00:01', '9999-12-31T23:59:59.999999-00:01'])
def test_offset_overflow_is_a_validation_error(value):
    with pytest.raises(ValidationError):
        SessionRead(expires_at=value)


def test_calendar_boundaries_remain_valid():
    for value in ('0001-01-01T00:00:00Z', '9999-12-31T23:59:59.999999Z', '0001-01-01T01:00:00+01:00'):
        assert SessionRead(expires_at=value).expires_at is not None


def test_import_overflow_refuses_without_internal_error_or_write(client):
    start(client)
    create(client)
    bundle=client.get('/api/v1/export').json()
    bundle['exportedAt']='0001-01-01T00:00:00+00:01'
    response=client.post('/api/v1/import',json={'bundle':bundle},headers=HEADERS|{'Idempotency-Key':'utc-boundary-001'})
    assert response.status_code==422
    assert len(client.get('/api/v1/watches').json())==1
