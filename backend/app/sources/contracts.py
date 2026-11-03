"""Adapter output: explicit unknowns and official order, never an admission prediction."""
import hashlib
import hmac
import json
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

class CandidateRow(BaseModel):
    model_config = ConfigDict(frozen=True, extra='forbid', strict=True, revalidate_instances='always')
    candidate_key: str = Field(pattern=r'^[a-f0-9]{64}$', repr=False)
    row_ref: str = Field(pattern=r'^[A-Za-z0-9_.:/-]{1,100}$')
    official_rank: int = Field(ge=1, le=1_000_000)
    score: Decimal | None = Field(default=None, ge=0, le=1000, decimal_places=2, allow_inf_nan=False)
    consent: bool | None = None
    priority: int | None = Field(default=None, ge=1, le=1000)
    participation: Literal['unknown', 'active', 'withdrawn', 'enrolled'] = 'unknown'


class ParsedList(BaseModel):
    model_config = ConfigDict(frozen=True, extra='forbid', strict=True, revalidate_instances='always')
    source_id: str = Field(min_length=1, max_length=36)
    group_id: str = Field(min_length=1, max_length=36)
    year: int = Field(ge=2000, le=2100)
    adapter_version: str = Field(pattern=r'^[A-Za-z0-9_.-]{1,80}$')
    kind: Literal['live', 'archive']
    complete: bool
    expected_rows: int | None = Field(default=None, ge=0, le=100_000)
    seats: int | None = Field(default=None, ge=0, le=1_000_000)
    source_updated_at: AwareDatetime | None = None
    entries: tuple[CandidateRow, ...] = Field(max_length=100_000, repr=False)
    warnings: tuple[Literal['no_source_timestamp', 'unknown_consent', 'unknown_priority'], ...] = ()


@dataclass(frozen=True)
class SourceBinding:
    source_id: str
    group_id: str
    year: int
    url: str
    domain: str
    adapter_version: str
    kind: Literal['live', 'archive']
    enabled: bool


def scoped_candidate_key(binding: SourceBinding, public_id: str, secret: bytes) -> str:
    if len(secret) < 32 or not public_id or len(public_id) > 200:
        raise ValueError('invalid_identity_input')
    value = json.dumps([binding.source_id, binding.group_id, binding.year, public_id], ensure_ascii=False, separators=(',', ':'))
    return hmac.new(secret, value.encode(), hashlib.sha256).hexdigest()


class AdapterError(Exception):
    """Only stable diagnostic codes may leave an adapter; no page text or IDs."""
    def __init__(self, code: str):
        allowed = {'operator_quarantine', 'unsupported_source', 'adapter_unavailable', 'invalid_format', 'invalid_binding', 'source_disabled', 'unattested_adapter'}
        self.code = code if code in allowed else 'invalid_format'
        super().__init__(self.code)
