from datetime import datetime
from typing import Literal

from pydantic import Field, HttpUrl, field_validator

from .calculation import CalculationInput, CalculationResult, CamelModel


class WatchCreate(CamelModel):
    university: str = Field(min_length=1, max_length=160)
    title: str = Field(min_length=1, max_length=200)
    source_url: HttpUrl = Field(max_length=2048)
    values: CalculationInput

    @field_validator('source_url')
    @classmethod
    def no_credentials_in_source(cls, value):
        if value.username or value.password:
            raise ValueError('Ссылка не должна содержать логин или пароль.')
        return value

    @field_validator('university', 'title')
    @classmethod
    def clean_title(cls, value):
        if not value.strip():
            raise ValueError('Название не может быть пустым.')
        return value.strip()


class SessionRead(CamelModel):
    expires_at: datetime


class UniversityRead(CamelModel):
    id: str
    name: str
    official_url: str
    provenance_url: str
    verified_at: datetime
    coverage: Literal['manual']


class CatalogRead(CamelModel):
    items: list[UniversityRead]
    total: int


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


class DataExport(CamelModel):
    format_version: Literal['manual-export-v1'] = 'manual-export-v1'
    exported_at: datetime
    watches: list[WatchDetail] = Field(max_length=20)


class HistoryPage(CamelModel):
    items: list[SnapshotRead]
    next_cursor: str | None
