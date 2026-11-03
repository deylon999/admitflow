"""Guest-scoped archive lookup and confirmation; no public list/raw endpoint."""
from datetime import datetime,timezone
from decimal import Decimal
from typing import Literal

from fastapi import Depends,HTTPException,Path
from pydantic import Field,field_validator
from sqlalchemy.orm import Session

from .admissions import Campaign,CandidateEntry,CompetitionGroup,PublishedSnapshot,Source,SourceSnapshot,University
from .calculation import CamelModel
from .database import BrowserSession
from .source_catalog import GroupRead,group_read
from .source_tokens import Confirmation,issue
from .sources.contracts import AdapterError,scoped_candidate_key
from .sources.publishing import binding_from_db,utc


class LookupInput(CamelModel):
    public_code:str=Field(min_length=1,max_length=64,pattern='^[A-Za-z0-9-]{1,64}$',repr=False)
    @field_validator('public_code',mode='before')
    @classmethod
    def trim(cls,value):return value.strip() if isinstance(value,str) else value


class CandidateFact(CamelModel):
    row_ref:str
    official_rank:int
    score:Decimal|None
    consent:bool|None
    priority:int|None
    participation:Literal['unknown','active','withdrawn','enrolled']


class LookupResult(CamelModel):
    group:GroupRead
    found:bool
    candidate:CandidateFact|None=None
    confirmation_token:str|None=Field(default=None,repr=False)
    expires_at:datetime|None=None


def available_source(db,source_id,registry):
    source=db.get(Source,source_id)
    if source is None:raise HTTPException(404,'Источник не найден.')
    binding=binding_from_db(db,source)
    try:registry.resolve(binding)
    except AdapterError:raise HTTPException(409,'Поиск в этом источнике сейчас недоступен. Можно сохранить направление вручную.') from None
    pointer=db.get(PublishedSnapshot,source_id)
    snapshot=db.get(SourceSnapshot,pointer.snapshot_id) if pointer else None
    if not snapshot or not snapshot.complete or not snapshot.normalized_hash or snapshot.adapter_version!=source.adapter_version:
        raise HTTPException(409,'Проверенный снимок источника ещё не получен.')
    group=db.get(CompetitionGroup,source.group_id);campaign=db.get(Campaign,group.campaign_id);university=db.get(University,campaign.university_id)
    return source,binding,snapshot,group_read(db,group,campaign,university,source,registry=registry)


def candidate_fact(row):
    return CandidateFact(row_ref=row.row_ref,official_rank=row.official_rank,score=row.score,consent=row.consent,priority=row.priority,participation=row.participation)


def install_source_routes(app,database,owner,write_owner,registry,key,clock):
    @app.post('/api/v1/sources/{source_id}/lookup',response_model=LookupResult)
    def lookup(body:LookupInput,source_id:str=Path(min_length=1,max_length=36),owner_hash:str=Depends(owner),db:Session=Depends(database)):
        if key is None:raise HTTPException(409,'Поиск источника не настроен.')
        source,binding,snapshot,group=available_source(db,source_id,registry)
        candidate_key=scoped_candidate_key(binding,body.public_code,key)
        row=db.get(CandidateEntry,(snapshot.id,candidate_key))
        if row is None:return LookupResult(group=group,found=False)
        now=clock();session=db.get(BrowserSession,owner_hash)
        expires=min(int(now.timestamp())+300,int(utc(session.expires_at).timestamp()))
        claims=Confirmation(version=1,source_id=source.id,group_id=source.group_id,snapshot_id=snapshot.id,candidate_key=candidate_key,expires=expires)
        return LookupResult(group=group,found=True,candidate=candidate_fact(row),confirmation_token=issue(claims,owner_hash,key),expires_at=datetime.fromtimestamp(expires,timezone.utc))
