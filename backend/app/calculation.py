from typing import Literal
from types import MappingProxyType

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra='forbid')


class CalculationInput(CamelModel):
    rank: int = Field(strict=True, ge=1, le=1_000_000)
    seats: int = Field(strict=True, ge=1, le=1_000_000)
    excluded: int = Field(strict=True, ge=0, le=1_000_000)
    no_consent: int = Field(strict=True, ge=0, le=1_000_000)

    @model_validator(mode='after')
    def check_people_above(self):
        if self.excluded + self.no_consent >= self.rank:
            raise ValueError('Группы выше вас не должны пересекаться, а их сумма должна быть меньше номера.')
        return self


class CalculationResult(CamelModel):
    place: int
    worst_place: int
    seats: int
    state: Literal['safe', 'conditional', 'out']
    status: str


class AssessmentInput(CamelModel):
    mode: Literal['manual', 'automatic', 'archive'] = 'manual'
    model_version: str = Field(default='manual-v1', max_length=80)
    values: CalculationInput | None = None


class ScenarioAssessment(CamelModel):
    state: Literal['ready', 'unsupported', 'insufficient_data']
    result: CalculationResult | None = None
    reason: str | None = None


def calculate_manual_v1(values: CalculationInput) -> CalculationResult:
    place = values.rank - values.excluded - values.no_consent
    worst = values.rank - values.excluded
    state = 'safe' if worst <= values.seats else 'conditional' if place <= values.seats else 'out'
    status = {
        'safe': 'В пределах мест в обоих рассмотренных сценариях',
        'conditional': 'В пределах мест только в текущем сценарии согласий',
        'out': 'За границей мест по введённым данным',
    }[state]
    return CalculationResult(place=place, worst_place=worst, seats=values.seats, state=state, status=status)


# New calculation versions must be added, never replace the historical callable.
MANUAL_CALCULATORS = MappingProxyType({'manual-v1': calculate_manual_v1})


def calculate_versioned(values: CalculationInput, version: str) -> CalculationResult:
    if version not in MANUAL_CALCULATORS:
        raise ValueError('unsupported_manual_version')
    return MANUAL_CALCULATORS[version](values)


def calculate(values: CalculationInput) -> CalculationResult:
    return calculate_versioned(values, 'manual-v1')


def assess_scenario(body: AssessmentInput) -> ScenarioAssessment:
    if body.mode != 'manual' or body.model_version != 'manual-v1':
        return ScenarioAssessment(state='unsupported', reason='Этот режим или версия правил ещё не поддерживается. Числовой вывод недоступен.')
    if body.values is None:
        return ScenarioAssessment(state='insufficient_data', reason='Недостаточно данных для расчёта. Заполните четыре числовых поля.')
    return ScenarioAssessment(state='ready', result=calculate(body.values))
