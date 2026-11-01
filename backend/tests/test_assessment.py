import json
from pathlib import Path

import pytest

CASES = json.loads((Path(__file__).resolve().parents[2] / 'shared/assessment-cases.json').read_text(encoding='utf-8'))


@pytest.mark.parametrize('case', CASES, ids=lambda case: case['name'])
def test_assessment_matches_shared_frontend_cases(client, case):
    response = client.post('/api/v1/assess', json=case['input'])
    assert response.status_code == 200
    result = response.json()
    assert result['state'] == case['state']
    if case['state'] != 'ready':
        assert result['result'] is None and result['reason']
    else:
        assert result['result']['place'] == 74
        assert result['result']['worstPlace'] == 90


def test_bad_numbers_remain_validation_errors(client):
    body = {'values': {'rank': -1, 'seats': 1, 'excluded': 0, 'noConsent': 0}}
    assert client.post('/api/v1/assess', json=body).status_code == 422
