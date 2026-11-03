"""Private in-app changes; reading never acknowledges an event."""
from datetime import datetime
from fastapi import Depends,HTTPException,Path,Query
from sqlalchemy import and_,func,or_,select
from sqlalchemy.orm import Session
from .admissions import Assessment,ChangeEvent,SourceSnapshot,Subscription,CompetitionGroup
from .calculation import CamelModel
from .scenario_api import ScenarioRead,read
from .sources.publishing import utc

class ChangeRead(CamelModel):
    id:str
    created_at:datetime
    seen_at:datetime|None
    title:str
    scenario:ScenarioRead

class ChangePage(CamelModel):
    items:list[ChangeRead]
    total:int
    unread_count:int
    next_cursor:str|None

def install(app,database,owner,write_owner,clock):
    def owned(owner_hash):
        return select(ChangeEvent,Assessment,SourceSnapshot,CompetitionGroup).join(Assessment,ChangeEvent.assessment_id==Assessment.id).join(Subscription,Assessment.subscription_id==Subscription.id).join(SourceSnapshot,Assessment.snapshot_id==SourceSnapshot.id).join(CompetitionGroup,Assessment.group_id==CompetitionGroup.id).where(Subscription.owner_hash==owner_hash)
    def dto(row):
        event,assessment,snapshot,group=row
        return ChangeRead(id=event.id,created_at=utc(event.created_at),seen_at=utc(event.seen_at) if event.seen_at else None,title=group.title,scenario=read(assessment,snapshot))
    @app.get('/api/v1/changes',response_model=ChangePage)
    def changes(before:str|None=Query(None,max_length=36),limit:int=Query(20,ge=1,le=50),unread:bool=False,owner_hash:str=Depends(owner),db:Session=Depends(database)):
        base=owned(owner_hash);query=base
        # Resolve before filtering unread, so acknowledging a cursor keeps it usable.
        if before:
            cursor=db.execute(base.where(ChangeEvent.id==before)).first()
            if cursor is None:raise HTTPException(400,'Курсор изменений недействителен.')
            event=cursor[0];query=query.where(or_(ChangeEvent.created_at<event.created_at,and_(ChangeEvent.created_at==event.created_at,ChangeEvent.id<before)))
        if unread:query=query.where(ChangeEvent.seen_at.is_(None))
        total=select(func.count()).select_from(base.subquery()).scalar_subquery()
        unseen=select(func.count()).select_from(base.where(ChangeEvent.seen_at.is_(None)).subquery()).scalar_subquery()
        rows=db.execute(query.add_columns(total,unseen).order_by(ChangeEvent.created_at.desc(),ChangeEvent.id.desc()).limit(limit+1)).all()
        counts=(rows[0][-2],rows[0][-1]) if rows else db.execute(select(total,unseen)).one()
        return ChangePage(items=[dto(row[:4]) for row in rows[:limit]],total=counts[0],unread_count=counts[1],next_cursor=rows[limit-1][0].id if len(rows)>limit else None)
    @app.post('/api/v1/changes/{event_id}/seen',response_model=ChangeRead)
    def seen(event_id:str=Path(max_length=36),owner_hash:str=Depends(write_owner),db:Session=Depends(database)):
        # Session owner lock serializes concurrent acknowledgements and deletion.
        row=db.execute(owned(owner_hash).where(ChangeEvent.id==event_id)).first()
        if row is None:raise HTTPException(404,'Изменение не найдено.')
        if row[0].seen_at is None:row[0].seen_at=clock()
        value=dto(row);db.commit();return value
