"""Candidate facts shared by lookup responses and persisted history."""

from decimal import Decimal
from typing import Literal

from app.core.schema_base import CamelModel


class CandidateFact(CamelModel):
    row_ref:str
    official_rank:int
    score:Decimal|None
    consent:bool|None
    priority:int|None
    participation:Literal['unknown','active','withdrawn','enrolled']


def candidate_fact(row):
    return CandidateFact(row_ref=row.row_ref,official_rank=row.official_rank,score=row.score,consent=row.consent,priority=row.priority,participation=row.participation)
