"""Public bounded group metadata, never raw lists or applicant identifiers."""
from datetime import datetime
from typing import Literal

from pydantic import Field
from sqlalchemy import select,func,or_,and_

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
    lookup_code_hint:str|None=Field(default=None,max_length=300)
    assessment_available:bool=False
    scenario_available:bool=False


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
    hint=None
    if source and available:
        from .sources.table_profiles import PROFILES
        profile=PROFILES.get(source.id)
        if profile and (profile.group_id,profile.year,profile.version)==(group.id,campaign.year,source.adapter_version):hint=profile.lookup_code_hint
    return GroupRead(id=group.id,university_id=university.id,university_name=university.name,parent_university_id=university.parent_id,
                     year=campaign.year,level=campaign.level,title=group.title,study_form=group.study_form,funding=group.funding,
                     category=group.category,seats=snapshot.seats if snapshot else group.seats,coverage=mode,source_id=source.id if source else None,
                     source_url=status['sourceUrl'] if status else None,source_state=status['state'] if status else None,
                     data_kind=status['dataKind'] if status else None,
                     snapshot_id=snapshot.id if snapshot else None,fetched_at=status['fetchedAt'] if status else None,
                     source_updated_at=status['sourceUpdatedAt'] if status else None,last_checked_at=status['lastCheckedAt'] if status else None,
                     row_count=snapshot.row_count if snapshot else None,lookup_available=lookup,
                     lookup_code_hint=hint,
                     scenario_available=bool(lookup and group.rules_version=='listed-consent-v1' and group.funding=='budget' and group.category=='general' and snapshot.seats and snapshot.seats>0))


def groups(db,*,q='',university_id='',branch_id='',year=None,after=None,limit=20,registry=PRODUCTION_REGISTRY):
    if type(limit) is not int or not 1<=limit<=50:raise ValueError('invalid_group_page_limit')
    def joined(statement):
        return statement.select_from(CompetitionGroup).join(Campaign,Campaign.id==CompetitionGroup.campaign_id).join(University,University.id==Campaign.university_id)
    facets=CatalogFacets(branches=[BranchRead(id=ident,name=name) for ident,name in db.execute(joined(select(University.id,University.name)).where(University.parent_id.is_not(None)).distinct().order_by(University.id))],
        years=list(db.scalars(joined(select(Campaign.year)).distinct().order_by(Campaign.year.desc()))))
    needle=q.strip().casefold()
    predicates=[]
    if university_id:predicates.append(or_(University.id==university_id,University.parent_id==university_id))
    if branch_id:predicates.append(University.parent_id.is_(None) if branch_id=='main' else and_(University.id==branch_id,University.parent_id.is_not(None)))
    if year is not None:predicates.append(Campaign.year==year)
    if needle:predicates.append((CompetitionGroup.search_text+' '+University.search_name).contains(needle,autoescape=True))
    total=db.scalar(joined(select(func.count(CompetitionGroup.id))).where(*predicates))
    # Match Python's original string order regardless of the database locale.
    ordered=CompetitionGroup.id.collate('C' if db.bind.dialect.name=='postgresql' else 'BINARY')
    statement=joined(select(CompetitionGroup,Campaign,University)).where(*predicates)
    if after is not None:statement=statement.where(ordered>after)
    rows=db.execute(statement.order_by(ordered).limit(limit+1)).all();page=rows[:limit]
    sources=[]
    if page:
        first=select(func.min(Source.id).label('id')).where(Source.group_id.in_([g.id for g,_,_ in page])).group_by(Source.group_id).subquery()
        sources=db.scalars(select(Source).join(first,Source.id==first.c.id)).all()
    by_group={source.group_id:source for source in sources}
    return GroupCatalog(items=[group_read(db,g,c,u,by_group.get(g.id),registry=registry) for g,c,u in page],total=total,
                        next_cursor=page[-1][0].id if len(rows)>limit else None,facets=facets)
