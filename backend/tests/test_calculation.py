import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.calculation import CalculationInput, calculate

FIXTURES = json.loads(
    (Path(__file__).resolve().parents[2] / 'shared/calculations.json').read_text(encoding='utf-8')
)
EXAMPLE = FIXTURES['valid'][0]['input']


@pytest.mark.parametrize('case', FIXTURES['valid'], ids=lambda case: case['name'])
def test_shared_scenarios(case):
    result = calculate(CalculationInput.model_validate(case['input'])).model_dump(by_alias=True)
    assert {key: result[key] for key in case['expected']} == case['expected']
    if result['state'] == 'safe':
        assert result['status'] == 'В пределах мест в обоих рассмотренных сценариях'


@pytest.mark.parametrize('case', FIXTURES['invalid'], ids=lambda case: case['name'])
def test_shared_invalid_input(case):
    with pytest.raises(ValidationError):
        CalculationInput.model_validate({**EXAMPLE, **case['patch']})


def test_api_requires_numbers_not_form_strings():
    with pytest.raises(ValidationError):
        CalculationInput.model_validate({**EXAMPLE, 'rank': '120'})
