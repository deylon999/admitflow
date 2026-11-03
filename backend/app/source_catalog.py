"""Public bounded group metadata, never raw lists or applicant identifiers."""
from datetime import datetime
from typing import Literal

from pydantic import Field
from sqlalchemy import select

from .admissions import Campaign,CompetitionGroup,Source,University
from .calculation import CamelModel
from .sources.registry import PRODUCTION_REGISTRY
from .sources.status import source_status


class GroupRead(CamelModel):
    id:str
    university_id:str
    university_name:str
    parent_university_id:str|None
    year:int
    level:str
    title:str
    study_form:str
    funding:str
    category:str
    seats:int|None
    coverage:Literal['manual','archive','automatic','unsupported']
    source_id:str|None=None
    source_url:str|None=None
    source_state:str|None=None
    data_kind:Literal['archive','live']|None=None
    snapshot_id:str|None=None
    fetched_at:datetime|None=None
    source_updated_at:datetime|None=None
    last_checked_at:datetime|None=None
    row_count:int|None=None
    lookup_available:bool=False
    assessment_available:bool=False


class BranchRead(CamelModel):
    id:str
    name:str


class CatalogFacets(CamelModel):
    branches:list[BranchRead]
    years:list[int]


class GroupCatalog(CamelModel):
    items:list[GroupRead]
    total:int
    next_cursor:str|None
    facets:CatalogFacets


def group_read(db,group,campaign,university,source,*,registry=PRODUCTION_REGISTRY):
    status=source_status(db,source.id,registry=registry) if source else None
    available=bool(status and status['adapterAvailable'])
    mode='manual' if group.coverage=='manual' else 'unsupported'
    if available:
        mode='archive' if status['dataKind']=='archive' else 'automatic' if group.coverage=='automatic' and group.rules_version else 'unsupported'
    from .admissions import SourceSnapshot
    snapshot=db.get(SourceSnapshot,status['publishedSnapshotId']) if status and status['publishedSnapshotId'] else None
    lookup=bool(available and snapshot and snapshot.complete and snapshot.normalized_hash and snapshot.adapter_version==source.adapter_version)
    return GroupRead(id=group.id,university_id=university.id,university_name=university.name,parent_university_id=university.parent_id,
                     year=campaign.year,level=campaign.level,title=group.title,study_form=group.study_form,funding=group.funding,
                     category=group.category,seats=snapshot.seats if snapshot else group.seats,coverage=mode,source_id=source.id if source else None,
                     source_url=status['sourceUrl'] if status else None,source_state=status['state'] if status else None,
                     data_kind=status['dataKind'] if status else None,
                     snapshot_id=snapshot.id if snapshot else None,fetched_at=status['fetchedAt'] if status else None,
                     source_updated_at=status['sourceUpdatedAt'] if status else None,last_checked_at=status['lastCheckedAt'] if status else None,
                     row_count=snapshot.row_count if snapshot else None,lookup_available=lookup)


def groups(db,*,q='',university_id='',branch_id='',year=None,after=None,limit=20,registry=PRODUCTION_REGISTRY):
    rows=db.execute(select(CompetitionGroup,Campaign,University).join(Campaign,Campaign.id==CompetitionGroup.campaign_id)
                    .join(University,University.id==Campaign.university_id)).all()
    facets=CatalogFacets(branches=[BranchRead(id=u.id,name=u.name) for u in {u.id:u for _,_,u in rows if u.parent_id}.values()],
                         years=sorted({c.year for _,c,_ in rows},reverse=True))
    needle=q.strip().casefold()
    filtered=[(g,c,u) for g,c,u in rows if (not university_id or u.id==university_id or u.parent_id==university_id)
              and (not branch_id or (u.parent_id is None if branch_id=='main' else u.id==branch_id and u.parent_id is not None))
              and (year is None or c.year==year) and (not needle or needle in f'{g.title} {g.official_id} {u.name}'.casefold())]
    filtered.sort(key=lambda row:row[0].id)
    remaining=[row for row in filtered if after is None or row[0].id>after]
    page=remaining[:limit]
    sources=db.scalars(select(Source).where(Source.group_id.in_([g.id for g,_,_ in page])).order_by(Source.id)).all() if page else []
    by_group={}
    for source in sources:by_group.setdefault(source.group_id,source)
    return GroupCatalog(items=[group_read(db,g,c,u,by_group.get(g.id),registry=registry) for g,c,u in page],total=len(filtered),
                        next_cursor=page[-1][0].id if len(remaining)>limit else None,facets=facets)
