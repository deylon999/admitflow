"""Read projections shared by archive, history and scenarios."""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from sqlalchemy import select, tuple_

from app.admissions import Assessment, Campaign, CandidateEntry, CompetitionGroup, Source, SourceSnapshot, University
from app.catalog.source_catalog import GroupRead, group_read
from app.core.schema_base import CamelModel
from app.core.time import utc


class CandidateFact(CamelModel):
    row_ref:str
    official_rank:int
    score:Decimal|None
    consent:bool|None
    priority:int|None
    participation:Literal['unknown','active','withdrawn','enrolled']


class ArchiveDirection(CamelModel):
    id:str
    created_at:datetime
    group:GroupRead
    candidate:CandidateFact|None
    confirmed_snapshot_id:str|None
    notice:str|None=None


def candidate_fact(row):
    return CandidateFact(row_ref=row.row_ref,official_rank=row.official_rank,score=row.score,consent=row.consent,priority=row.priority,participation=row.participation)


def archive_directions(db,values,registry):
    """Bounded batch reads; resolve each source pointer once per response."""
    if not values:return []
    identities={value.id for value in values};group_ids={value.group_id for value in values}
    confirmations=db.execute(select(Assessment,SourceSnapshot).join(SourceSnapshot,Assessment.snapshot_id==SourceSnapshot.id).where(
        Assessment.subscription_id.in_(identities),Assessment.rules_version=='source-confirmation-v1').order_by(Assessment.assessed_at,Assessment.id)).all()
    initial={}
    for assessment,snapshot in confirmations:initial.setdefault(assessment.subscription_id,snapshot)
    groups={g.id:(g,c,u) for g,c,u in db.execute(select(CompetitionGroup,Campaign,University).join(Campaign,CompetitionGroup.campaign_id==Campaign.id)
             .join(University,Campaign.university_id==University.id).where(CompetitionGroup.id.in_(group_ids))).all()}
    sources=db.scalars(select(Source).where(Source.group_id.in_(group_ids))).all()
    by_source={source.id:source for source in sources};by_group={}
    for source in sources:by_group.setdefault(source.group_id,[]).append(source)
    metadata={};selected={}
    for value in values:
        confirmed=initial.get(value.id);source=by_source.get(confirmed.source_id) if confirmed else None
        fallback=by_group.get(value.group_id,[])
        if source is None and len(fallback)==1:source=fallback[0]
        identity=(value.group_id,source.id if source else None)
        if identity not in metadata:metadata[identity]=group_read(db,*groups[value.group_id],source,registry=registry)
        selected[value.id]=metadata[identity]
    pairs={(selected[value.id].snapshot_id,value.candidate_key) for value in values if selected[value.id].snapshot_id}
    entries=db.scalars(select(CandidateEntry).where(tuple_(CandidateEntry.snapshot_id,CandidateEntry.candidate_key).in_(pairs))).all() if pairs else []
    rows={(row.snapshot_id,row.candidate_key):row for row in entries};result=[]
    for value in values:
        meta=selected[value.id];row=rows.get((meta.snapshot_id,value.candidate_key));confirmed=initial.get(value.id)
        result.append(ArchiveDirection(id=value.id,created_at=utc(value.created_at),group=meta,candidate=candidate_fact(row) if row else None,
            confirmed_snapshot_id=confirmed.id if confirmed else None,
            notice=None if row else 'Запись отсутствует в доступном снимке. Это не подтверждает отзыв заявления или отказ в зачислении.'))
    return result
