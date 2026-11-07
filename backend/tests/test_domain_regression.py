"""T042: every mandatory domain case from docs/QUALITY.md has an explicit expected outcome.

Map of case -> proof lives in docs/evidence/regression.md. The last test keeps that map honest.
"""
from dataclasses import dataclass, replace
from pathlib import Path
import re

from pydantic import ValidationError
import pytest

from app.calculation import CalculationInput, calculate
from app.scenarios import assess
from app.sources.contracts import scoped_candidate_key
from app.sources.validation import Quarantined, validate_list
from source_helpers import BINDING, NOW, parsed

SECRET = b'k'*32


@dataclass
class Row:
    candidate_key: str
    official_rank: int
    consent: bool | None = None
    participation: str = 'unknown'
    score: str | None = None


def ranked(*rows):
    return [replace(row, candidate_key=f'c{index}', official_rank=index) for index, row in enumerate(rows, 1)]


def row(consent=None, participation='unknown', score=None):
    return Row('', 0, consent, participation, score)


def scenario(data, key=None, **changes):
    return assess(data, key or data[-1].candidate_key, **({'funding': 'budget', 'category': 'general', 'seats': 2} | changes))


def test_d01_people_outside_competition_are_not_subtracted_again():
    # Absent rows are never inferred: only rows present in this list can change a place.
    result = scenario(ranked(row(True), row(True), row(True)), seats=3)
    assert result.numbers.all_consent_place == 3 and result.numbers.withdrawn_above == 0
    manual = calculate(CalculationInput(rank=120, seats=90, excluded=30, no_consent=16))
    assert (manual.place, manual.worst_place, manual.state) == (74, 90, 'safe')


def test_d02_person_with_two_reasons_is_subtracted_once():
    result = scenario(ranked(row(False, 'withdrawn'), row(True), row(True)), seats=2)
    numbers = result.numbers
    assert (numbers.withdrawn_above, numbers.consent_no_above, numbers.consent_yes_above) == (1, 0, 1)
    assert numbers.all_consent_place == 2
    with pytest.raises(ValidationError):
        CalculationInput(rank=10, seats=5, excluded=5, no_consent=5)


def test_d03_new_consent_changes_new_result_and_not_the_previous_one():
    before_rows = ranked(row(False), row(False), row(True))
    before = scenario(before_rows, seats=1)
    stored = before.model_dump()
    after_rows = ranked(row(True), row(False), row(True))
    after = scenario(after_rows, seats=1)
    assert before.state == 'conditional' and after.state == 'out'
    assert before.model_dump() == stored and before.numbers.current_lower == 1


def test_d04_withdrawn_and_missing_consent_are_different_states():
    withdrawn = scenario(ranked(row(None, 'withdrawn'), row(True)), seats=1)
    no_consent = scenario(ranked(row(False), row(True)), seats=1)
    assert withdrawn.state == 'within' and withdrawn.numbers.all_consent_place == 1
    assert no_consent.state == 'conditional' and no_consent.numbers.all_consent_place == 2
    assert scenario(ranked(row(True, 'withdrawn')), seats=5).reason_codes == ['candidate_withdrawn']


@pytest.mark.parametrize('changes', [{'source_id': 'other'}, {'group_id': 'other'}, {'year': 2025}])
def test_d05_same_public_id_does_not_merge_people_between_scopes(changes):
    base = scoped_candidate_key(BINDING, '123-456', SECRET)
    assert base == scoped_candidate_key(BINDING, '123-456', SECRET)
    assert base != scoped_candidate_key(replace(BINDING, **changes), '123-456', SECRET)


def test_d06_unknown_priority_never_produces_an_official_result():
    result = scenario(ranked(row(True), row(True)), seats=5)
    assert 'priorities_not_applied' in result.reason_codes
    assert result.official_result_available is False
    assert parsed().entries[0].priority is None


@pytest.mark.parametrize(('seats', 'state', 'code'), [(0, 'insufficient_data', 'missing_or_zero_capacity'), (None, 'insufficient_data', 'missing_or_zero_capacity')])
def test_d07_missing_or_zero_capacity_refuses_without_numbers(seats, state, code):
    result = scenario(ranked(row(True)), seats=seats)
    assert (result.state, result.reason_codes, result.numbers) == (state, [code], None)


@pytest.mark.parametrize(('before', 'after', 'code'), [(100, 40, 'capacity_drop'), (16, 16000, 'capacity_growth'), (16, 33, 'capacity_growth')])
def test_d07_erroneous_capacity_is_quarantined_against_previous(before, after, code):
    with pytest.raises(Quarantined, match=f'^{code}$'):
        validate_list(parsed().model_copy(update={'seats': after}), BINDING, NOW, previous=parsed().model_copy(update={'seats': before}))


@pytest.mark.parametrize(('before', 'after'), [(16, 20), (16, 32), (2, 5), (0, 100)])
def test_d07_ordinary_capacity_change_is_accepted(before, after):
    assert validate_list(parsed().model_copy(update={'seats': after}), BINDING, NOW, previous=parsed().model_copy(update={'seats': before}))


@pytest.mark.parametrize('seats', [21, 4, 16000])
def test_d07_first_publication_is_compared_with_reviewed_capacity(seats):
    with pytest.raises(Quarantined, match='^capacity_mismatch$'):
        validate_list(parsed().model_copy(update={'seats': seats}), BINDING, NOW, reviewed_seats=10)
    assert validate_list(parsed().model_copy(update={'seats': 12}), BINDING, NOW, reviewed_seats=10)


@pytest.mark.parametrize(('changes', 'code'), [({'complete': False}, 'incomplete_list'), ({'expected_rows': 999}, 'row_count_mismatch')])
def test_d09_incomplete_pagination_is_refused(changes, code):
    with pytest.raises(Quarantined, match=f'^{code}$'):
        validate_list(parsed().model_copy(update=changes), BINDING, NOW)


def test_q03_equal_scores_keep_official_order_and_do_not_reorder():
    data = ranked(row(True, score='270'), row(True, score='270'), row(True, score='270'))
    assert scenario(data, 'c2', seats=1).numbers.current_lower == 2
    assert scenario(data, 'c1', seats=1).numbers.current_lower == 1


def test_q03_unknown_consent_gives_bounds_and_no_decision_across_capacity():
    result = scenario(ranked(row(None), row(None), row(True)), seats=2)
    assert result.state == 'insufficient_data' and 'unknown_consent_crosses_capacity' in result.reason_codes
    assert (result.numbers.current_lower, result.numbers.current_upper) == (1, 3)


@pytest.mark.parametrize(('changes', 'code'), [({'funding': 'contract'}, 'unsupported_funding'), ({'category': 'quota'}, 'unsupported_category')])
def test_q03_unsupported_competition_is_refused_without_numbers(changes, code):
    result = scenario(ranked(row(True)), **changes)
    assert (result.state, result.reason_codes, result.numbers) == ('unsupported', [code], None)


@pytest.mark.parametrize('data', [[], [Row('a', 2)], [Row('a', 1), Row('a', 2)]])
def test_q03_incomplete_fields_and_broken_order_are_refused(data):
    assert assess(data, 'a', funding='budget', category='general', seats=2).reason_codes == ['incomplete_official_order']


def test_q03_candidate_absent_from_list_is_not_treated_as_withdrawal():
    result = scenario(ranked(row(True)), 'unknown', seats=2)
    assert result.reason_codes == ['candidate_not_in_snapshot'] and result.numbers is None


def test_retired_calculators_are_not_public_api(client):
    paths = client.get('/api/openapi.json').json()['paths']
    for path in ('/api/v1/calculate', '/api/v1/assess'):
        assert path not in paths
        assert client.post(path, json={}, headers={'X-Requested-With': 'abiturient'}).status_code == 404


def test_regression_map_points_at_existing_tests():
    tests = Path(__file__).parent
    document = (tests.parents[1]/'docs/evidence/regression.md').read_text(encoding='utf-8')
    references = re.findall(r'`([a-z_]+\.py)::([A-Za-z0-9_]+)`', document)
    assert len(references) >= 12
    for filename, name in references:
        assert re.search(rf'^def {name}\(', (tests/filename).read_text(encoding='utf-8'), re.M), f'{filename}::{name}'
    assert all(f'D{index:02}' in document for index in range(1, 13))


def naive(rows, key, seats):
    """Independent restatement of listed-consent-v1 for the prepared implementation."""
    candidate = next(item for item in rows if item.candidate_key == key)
    active = [item for item in rows[:candidate.official_rank-1] if item.participation != 'withdrawn']
    yes = sum(item.consent is True for item in active)
    unknown = sum(item.consent is None for item in active)
    return yes+1, yes+unknown+1, len(active)+1


def test_prepared_rows_match_independent_calculation_for_every_candidate():
    from random import Random
    from app.scenarios import PreparedRows
    generator = Random(173)
    for _ in range(30):
        rows = ranked(*(row(generator.choice([True, False, None]), generator.choice(['unknown', 'active', 'withdrawn', 'enrolled'])) for _ in range(generator.randint(1, 40))))
        prepared = PreparedRows(rows)
        seats = generator.randint(1, 20)
        for item in rows:
            if item.participation == 'withdrawn':
                continue
            result = assess(prepared, item.candidate_key, funding='budget', category='general', seats=seats)
            numbers = result.numbers
            assert (numbers.current_lower, numbers.current_upper, numbers.all_consent_place) == naive(rows, item.candidate_key, seats)
            assert result == assess(rows, item.candidate_key, funding='budget', category='general', seats=seats)
