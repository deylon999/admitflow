"""Fail closed on structural problems; quality signals require operator review."""
import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta

from pydantic import ValidationError

from .contracts import ParsedList, SourceBinding


class Quarantined(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class QualityPolicy:
    max_drop_fraction: float = 0.5
    drop_check_min_rows: int = 10
    max_capacity_growth: float = 2.0
    capacity_growth_min_delta: int = 10

    def __post_init__(self):
        if not 0 <= self.max_drop_fraction < 1 or self.drop_check_min_rows < 1 or self.max_capacity_growth <= 1 or self.capacity_growth_min_delta < 1:
            raise ValueError('invalid_quality_policy')


@dataclass(frozen=True)
class ValidatedList:
    parsed: ParsedList
    normalized_hash: str


def validate_list(value: ParsedList, binding: SourceBinding, fetched_at: datetime, *, previous: ParsedList | None = None, policy=QualityPolicy(), reviewed_seats: int | None = None) -> ValidatedList:
    try:
        parsed = ParsedList.model_validate(value)
    except (ValidationError, TypeError):
        raise Quarantined('invalid_schema') from None
    if (parsed.source_id,parsed.group_id,parsed.year,parsed.adapter_version,parsed.kind) != (binding.source_id,binding.group_id,binding.year,binding.adapter_version,binding.kind):
        raise Quarantined('identity_mismatch')
    if fetched_at.tzinfo is None or fetched_at.utcoffset() is None:
        raise Quarantined('invalid_fetch_time')
    if not parsed.complete:
        raise Quarantined('incomplete_list')
    if parsed.expected_rows is not None and parsed.expected_rows != len(parsed.entries):
        raise Quarantined('row_count_mismatch')
    if not parsed.entries and parsed.expected_rows != 0:
        raise Quarantined('unconfirmed_empty_list')
    if len({row.candidate_key for row in parsed.entries}) != len(parsed.entries):
        raise Quarantined('duplicate_candidate')
    if len({row.row_ref for row in parsed.entries}) != len(parsed.entries):
        raise Quarantined('duplicate_reference')
    if any(row.official_rank != index for index,row in enumerate(parsed.entries,1)):
        raise Quarantined('invalid_official_order')
    if parsed.source_updated_at and parsed.source_updated_at > fetched_at + timedelta(minutes=5):
        raise Quarantined('future_source_time')
    if previous is None and reviewed_seats and parsed.seats is not None:
        # A first publication has no history, so compare with the human-reviewed group capacity.
        if parsed.seats > reviewed_seats*policy.max_capacity_growth or parsed.seats < reviewed_seats*(1-policy.max_drop_fraction):
            raise Quarantined('capacity_mismatch')
    if previous:
        if previous.source_id != parsed.source_id or previous.group_id != parsed.group_id or previous.year != parsed.year:
            raise Quarantined('previous_identity_mismatch')
        if previous.source_updated_at and parsed.source_updated_at and parsed.source_updated_at < previous.source_updated_at:
            raise Quarantined('source_time_regressed')
        if len(previous.entries) >= policy.drop_check_min_rows and len(parsed.entries) < len(previous.entries) * (1-policy.max_drop_fraction):
            raise Quarantined('row_count_drop')
        if previous.seats and parsed.seats is not None and parsed.seats < previous.seats * (1-policy.max_drop_fraction):
            raise Quarantined('capacity_drop')
        if previous.seats and parsed.seats is not None and parsed.seats > previous.seats*policy.max_capacity_growth and parsed.seats-previous.seats >= policy.capacity_growth_min_delta:
            # An inflated place count would otherwise turn every candidate into a positive status.
            raise Quarantined('capacity_growth')
    canonical = parsed.model_dump_json()
    return ValidatedList(parsed, hashlib.sha256(canonical.encode()).hexdigest())
