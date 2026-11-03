from dataclasses import dataclass,replace
import pytest
from app.scenarios import VERSION,assess

@dataclass
class Row:
    candidate_key:str
    official_rank:int
    consent:bool|None
    participation:str='unknown'


def rows(*consents):return [Row(str(i),i,c) for i,c in enumerate(consents,1)]


def run(data,key=None,**changes):
    return assess(data,key or str(len(data)),**({'funding':'budget','category':'general','seats':2}|changes))


def test_current_and_all_consent_keep_official_order_without_double_deduction():
    data=rows(True,False,True,False)
    result=run(data,seats=3)
    assert result.state=='conditional' and result.numbers.current_lower==3 and result.numbers.all_consent_place==4
    assert result.numbers.withdrawn_above==0
    data[1].participation='withdrawn';result=run(data,seats=3)
    assert result.state=='within' and result.numbers.current_lower==3 and result.numbers.all_consent_place==3
    assert result.numbers.withdrawn_above==1 and 'own_consent_assumed' in result.reason_codes


def test_unknown_consent_crossing_capacity_returns_bounds_without_decision():
    result=run(rows(True,None,False),seats=2)
    assert result.state=='insufficient_data' and (result.numbers.current_lower,result.numbers.current_upper)==(2,3)
    assert 'unknown_consent_crosses_capacity' in result.reason_codes
    assert 'unknown_participation_included' in result.reason_codes and not result.official_result_available


@pytest.mark.parametrize('context,reason',[({'funding':'contract'},'unsupported_funding'),({'category':'quota'},'unsupported_category'),({'seats':0},'missing_or_zero_capacity'),({'seats':None},'missing_or_zero_capacity'),({'model_version':'unknown-v2'},'unsupported_model_version')])
def test_unsupported_and_missing_conditions_do_not_generate_numbers(context,reason):
    value=run(rows(True,False),**context)
    assert value.numbers is None and reason in value.reason_codes


def test_missing_candidate_and_broken_order_are_not_withdrawal_or_success():
    value=run(rows(True,False),key='not-listed');assert value.state=='insufficient_data' and 'candidate_not_in_snapshot' in value.reason_codes
    value=run([Row('1',2,True)]);assert value.numbers is None and 'incomplete_official_order' in value.reason_codes


def test_boundaries_and_outcome_are_conditional_not_official():
    assert run(rows(False),seats=1).state=='within'
    assert run(rows(True,True,False),seats=1).state=='out'
    assert run(rows(False,False,False),seats=1).state=='conditional'
    value=run(rows(True,False));assert value.model_version==VERSION and 'priorities_not_applied' in value.reason_codes


def test_unknown_withdrawal_and_consent_combinations_keep_valid_bounds():
    from itertools import product
    for consents in product([True,False,None],repeat=3):
        for excluded in product([True,False],repeat=2):
            data=rows(*consents)
            for row,withdrawn in zip(data,excluded):row.participation='withdrawn' if withdrawn else 'unknown'
            result=run(data,seats=2);n=result.numbers
            assert 1<=n.current_lower<=n.current_upper<=n.all_consent_place<=3
            assert n.consent_yes_above+n.consent_no_above+n.consent_unknown_above+n.withdrawn_above==2


def test_capacity_diff_and_model_version_are_explicit():
    from app.scenario_storage import difference
    first=run(rows(True,False,False),seats=2).model_dump(mode='json',by_alias=True)
    second=run(rows(True,False,False),seats=1).model_dump(mode='json',by_alias=True)
    changes=difference({'result':first,'candidate':None},{'result':second,'candidate':None})
    assert {'field':'seats','before':2,'after':1} in changes
    assert {'field':'state','before':'conditional','after':'out'} in changes
