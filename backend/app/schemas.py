from datetime import datetime
from typing import Literal

from pydantic import Field, HttpUrl, field_validator

from .calculation import CalculationInput, CalculationResult, CamelModel


class WatchCreate(CamelModel):
    university: str = Field(min_length=1, max_length=160)
    title: str = Field(min_length=1, max_length=200)
    source_url: HttpUrl = Field(max_length=2048)
    values: CalculationInput

    @field_validator('university', 'title')
    @classmethod
    def clean_title(cls, value):
        if not value.strip():
            raise ValueError('Название не может быть пустым.')
        return value.strip()


class SnapshotRead(CamelModel):
    id: str
    captured_at: datetime
    source_kind: Literal['manual']
    model_version: str
    values: CalculationInput
    calculation: CalculationResult


class WatchRead(CamelModel):
    id: str
    university: str
    title: str
    source_url: str
    created_at: datetime
    latest: SnapshotRead


class WatchDetail(WatchRead):
    history: list[SnapshotRead]
