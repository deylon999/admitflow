from typing import Literal

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


def calculate(values: CalculationInput) -> CalculationResult:
    place = values.rank - values.excluded - values.no_consent
    worst = values.rank - values.excluded
    state = 'safe' if worst <= values.seats else 'conditional' if place <= values.seats else 'out'
    status = {
        'safe': 'В пределах мест в обоих рассмотренных сценариях',
        'conditional': 'Сейчас проходите. Новые согласия могут изменить место',
        'out': 'Сейчас не проходите на бюджет',
    }[state]
    return CalculationResult(place=place, worst_place=worst, seats=values.seats, state=state, status=status)
