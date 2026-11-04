"""Versioned conditional scenario from one ordered competition list;not admission."""
from types import MappingProxyType
from typing import Literal
from .calculation import CamelModel

VERSION='listed-consent-v1'
ASSUMPTIONS=[
    'Сценарий относится только к указанному датированному списку одной конкурсной группы.',
    'Предполагается ваше согласие на зачисление;сервис не подаёт и не меняет согласие.',
    'Приоритеты между группами и специальные правила зачисления здесь не применяются.',
    'Все строки с неизвестным статусом участия сохраняются в расчёте;скрытые причины выбытия не предполагаются.',
    'Состав списка и число мест считаются неизменными. Это условный сценарий,не официальный результат и не вероятность.',
]


class ScenarioNumbers(CamelModel):
    current_lower:int
    current_upper:int
    all_consent_place:int
    seats:int
    consent_yes_above:int
    consent_no_above:int
    consent_unknown_above:int
    withdrawn_above:int


class ScenarioResult(CamelModel):
    model_version:str=VERSION
    state:Literal['within','conditional','out','unsupported','insufficient_data']
    numbers:ScenarioNumbers|None=None
    reason_codes:list[str]
    assumptions:list[str]
    official_result_available:Literal[False]=False


class PreparedRows:
    """One O(n) pass over an ordered list, then O(1) per candidate during publication."""
    def __init__(self,rows):
        rows=list(rows)
        self.count=len(rows)
        self.by_key={row.candidate_key:row for row in rows}
        self.ordered=bool(rows) and len(self.by_key)==len(rows) and all(row.official_rank==index for index,row in enumerate(rows,1))
        # Counters of rows strictly above each official rank; explicit withdrawals are excluded once.
        self.above=[(0,0,0,0,0)]
        yes=no=unknown=withdrawn=unknown_participation=0
        for row in rows:
            if row.participation=='withdrawn':
                withdrawn+=1
            else:
                yes+=row.consent is True
                no+=row.consent is False
                unknown+=row.consent is None
                unknown_participation+=row.participation=='unknown'
            self.above.append((yes,no,unknown,withdrawn,unknown_participation))


def assess_v1(rows,candidate_key,*,funding,category,seats):
    def refused(code,state='unsupported'):
        return ScenarioResult(state=state,reason_codes=[code],assumptions=list(ASSUMPTIONS))
    if funding!='budget':return refused('unsupported_funding')
    if category!='general':return refused('unsupported_category')
    if seats is None or seats<=0:return refused('missing_or_zero_capacity','insufficient_data')
    prepared=rows if isinstance(rows,PreparedRows) else PreparedRows(rows)
    if not prepared.ordered:return refused('incomplete_official_order','insufficient_data')
    candidate=prepared.by_key.get(candidate_key)
    if candidate is None:return refused('candidate_not_in_snapshot','insufficient_data')
    if candidate.participation=='withdrawn':return refused('candidate_withdrawn')
    yes,no,unknown,withdrawn,unknown_participation=prepared.above[candidate.official_rank-1]
    lower,upper,worst=yes+1,yes+unknown+1,yes+no+unknown+1
    state='within' if worst<=seats else 'out' if lower>seats else 'conditional' if upper<=seats else 'insufficient_data'
    reasons=['listed_consent_scenario','priorities_not_applied']
    if candidate.consent is not True:reasons.append('own_consent_assumed')
    if unknown_participation:reasons.append('unknown_participation_included')
    if unknown:reasons.append('unknown_consent_bounds')
    if state=='insufficient_data':reasons.append('unknown_consent_crosses_capacity')
    return ScenarioResult(state=state,numbers=ScenarioNumbers(current_lower=lower,current_upper=upper,all_consent_place=worst,seats=seats,consent_yes_above=yes,consent_no_above=no,consent_unknown_above=unknown,withdrawn_above=withdrawn),reason_codes=reasons,assumptions=list(ASSUMPTIONS))


MODELS=MappingProxyType({VERSION:assess_v1})


def assess(rows,key,*,model_version=VERSION,**context):
    model=MODELS.get(model_version)
    if model is None:return ScenarioResult(model_version=model_version,state='unsupported',reason_codes=['unsupported_model_version'],assumptions=list(ASSUMPTIONS))
    return model(rows,key,**context)
