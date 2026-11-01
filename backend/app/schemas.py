from datetime import datetime, timezone
from typing import Annotated, Literal
import re

from pydantic import AfterValidator, AwareDatetime, BeforeValidator, Field, HttpUrl, field_validator

from .calculation import CalculationInput, CalculationResult, CamelModel


def manual_timestamp(value):
    if isinstance(value, datetime):
        return value
    if not isinstance(value,str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})',value):
        raise ValueError('Требуется ISO-дата с часовым поясом и точностью до микросекунд.')
    return value


def representable_utc(value):
    try:
        value.astimezone(timezone.utc)
    except (OverflowError, ValueError):
        raise ValueError('Дата в UTC должна быть в пределах годов 0001–9999.') from None
    return value


ManualTimestamp = Annotated[AwareDatetime, BeforeValidator(manual_timestamp), AfterValidator(representable_utc)]


class ValidationProblem(CamelModel):
    detail: str
    fields: list[list[str | int]] = Field(max_length=20)
    truncated: bool


class WatchCreate(CamelModel):
    university: str = Field(min_length=1, max_length=160)
    title: str = Field(min_length=1, max_length=200)
    source_url: HttpUrl = Field(max_length=2048)
    values: CalculationInput

    @field_validator('university', 'title', 'source_url', mode='before')
    @classmethod
    def reject_controls(cls, value):
        if isinstance(value, str) and any(ord(char) < 32 or ord(char) == 127 for char in value):
            raise ValueError('Название и ссылка не должны содержать управляющие символы.')
        return value

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
    expires_at: ManualTimestamp


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
    captured_at: ManualTimestamp
    source_kind: Literal['manual']
    model_version: str
    values: CalculationInput
    calculation: CalculationResult


class WatchRead(CamelModel):
    id: str
    university: str
    title: str
    source_url: str
    created_at: ManualTimestamp
    latest: SnapshotRead


class WatchDetail(WatchRead):
    history: list[SnapshotRead] = Field(min_length=1,max_length=500)


class DataExport(CamelModel):
    format_version: Literal['manual-export-v1'] = 'manual-export-v1'
    exported_at: ManualTimestamp
    watches: list[WatchDetail] = Field(max_length=20)


class ImportRequest(CamelModel):
    bundle: DataExport


class ImportResult(CamelModel):
    imported_count: int
    snapshot_count: int
    replayed: bool = False


class CoverageRead(CamelModel):
    catalog_universities: int = Field(ge=0)
    automatic_sources: int = Field(ge=0)
    published_groups: int = Field(ge=0)
    fresh_groups: int = Field(ge=0)
    archive_groups: int = Field(ge=0)
    national_total: None
    generated_at: datetime


class HistoryPage(CamelModel):
    items: list[SnapshotRead]
    next_cursor: str | None
    total: int = Field(ge=1, le=500)


class SourceStatus(CamelModel):
    source_id: str
    group_id: str
    season: int
    state: Literal['fresh','stale','source_error','quarantined','archived','unknown','disabled','unsupported']
    data_kind: Literal['live','archive']
    worker_state: Literal['unknown','queued','running','idle','failed','expired']
    enabled: bool
    adapter_available: bool
    assessment_available: Literal[False]
    source_url: str | None
    adapter_version: str | None
    published_snapshot_id: str | None
    last_checked_at: datetime | None
    last_successful_check_at: datetime | None
    fetched_at: datetime | None
    source_updated_at: datetime | None
    freshness_seconds: int
