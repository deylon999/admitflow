"""Owner-scoped immutable conditional scenarios;GET never calculates or writes."""
from datetime import datetime
from typing import Any
from fastapi import Depends,HTTPException,Path,Query
from sqlalchemy import and_,func,or_,select
from sqlalchemy.orm import Session
from .admissions import Assessment,SourceSnapshot,Subscription
from .schema_base import CamelModel
from .scenarios import VERSION,ScenarioResult
from .scenario_explanations import Explanation,explain
from .sources.publishing import utc


class Change(CamelModel):
    field:str
    before:Any
    after:Any


class ScenarioRead(CamelModel):
    subscription_id:str
    group_id:str
    source_id:str|None=None
    available:bool
    id:str|None=None
    snapshot_id:str|None=None
    fetched_at:datetime|None=None
    source_updated_at:datetime|None=None
    assessed_at:datetime|None=None
    result:ScenarioResult|None=None
    changes:list[Change]=[]
    notice:str|None=None
    explanation:Explanation|None=None
    previous_id:str|None=None


class ScenarioPage(CamelModel):
    items:list[ScenarioRead]
    total:int
    next_cursor:str|None


def read(assessment,snapshot):
    result=ScenarioResult.model_validate(assessment.facts['result'])
    explanation=Explanation.model_validate(assessment.facts['explanation']) if assessment.facts.get('explanation') else explain(result,assessment.facts['diff'])
    return ScenarioRead(subscription_id=assessment.subscription_id,group_id=assessment.group_id,source_id=snapshot.source_id,available=True,id=assessment.id,snapshot_id=snapshot.id,fetched_at=utc(snapshot.fetched_at),source_updated_at=utc(snapshot.source_updated_at) if snapshot.source_updated_at else None,
        assessed_at=utc(assessment.assessed_at),result=result,changes=[Change.model_validate(x) for x in assessment.facts['diff']],explanation=explanation,previous_id=assessment.facts.get('previousAssessmentId'))


def install(app,database,owner,registry):
    def own(db,id,owner_hash):
        value=db.scalar(select(Subscription).where(Subscription.id==id,Subscription.owner_hash==owner_hash))
        if value is None:raise HTTPException(404,'Направление не найдено.')
        return value
    @app.get('/api/v1/subscriptions/{subscription_id}/scenario',response_model=ScenarioRead)
    def scenario(subscription_id:str=Path(max_length=36),owner_hash:str=Depends(owner),db:Session=Depends(database)):
        from .source_api import archive_directions
        value=own(db,subscription_id,owner_hash);record=archive_directions(db,[value],registry)[0]
        assessment=db.scalar(select(Assessment).where(Assessment.subscription_id==value.id,Assessment.snapshot_id==record.group.snapshot_id,Assessment.rules_version==VERSION))
        if assessment is None:return ScenarioRead(subscription_id=value.id,group_id=value.group_id,source_id=record.group.source_id,available=False,snapshot_id=record.group.snapshot_id,notice='Для этого снимка ещё нет проверенного условного сценария.')
        return read(assessment,db.get(SourceSnapshot,assessment.snapshot_id))
    @app.get('/api/v1/subscriptions/{subscription_id}/scenarios/{assessment_id}',response_model=ScenarioRead)
    def detail(subscription_id:str=Path(max_length=36),assessment_id:str=Path(max_length=36),owner_hash:str=Depends(owner),db:Session=Depends(database)):
        value=own(db,subscription_id,owner_hash)
        assessment=db.scalar(select(Assessment).where(Assessment.subscription_id==value.id,Assessment.id==assessment_id,Assessment.rules_version==VERSION))
        if assessment is None:raise HTTPException(404,'Версия сценария не найдена.')
        return read(assessment,db.get(SourceSnapshot,assessment.snapshot_id))
    @app.get('/api/v1/subscriptions/{subscription_id}/scenario-history',response_model=ScenarioPage)
    def history(subscription_id:str=Path(max_length=36),before:str|None=Query(None,max_length=36),limit:int=Query(20,ge=1,le=100),owner_hash:str=Depends(owner),db:Session=Depends(database)):
        value=own(db,subscription_id,owner_hash)
        query=select(Assessment,SourceSnapshot).join(SourceSnapshot,Assessment.snapshot_id==SourceSnapshot.id).where(Assessment.subscription_id==value.id,Assessment.rules_version==VERSION)
        total=db.scalar(select(func.count()).select_from(query.subquery()))
        if before:
            cursor=db.execute(query.where(Assessment.id==before)).first()
            if cursor is None:raise HTTPException(400,'Курсор сценариев недействителен.')
            snapshot=cursor[1];query=query.where(or_(SourceSnapshot.fetched_at<snapshot.fetched_at,and_(SourceSnapshot.fetched_at==snapshot.fetched_at,Assessment.id<before)))
        rows=db.execute(query.order_by(SourceSnapshot.fetched_at.desc(),Assessment.id.desc()).limit(limit+1)).all()
        return ScenarioPage(items=[read(a,s) for a,s in rows[:limit]],total=total,next_cursor=rows[limit-1][0].id if len(rows)>limit else None)
