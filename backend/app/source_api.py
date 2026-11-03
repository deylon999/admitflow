"""Guest-scoped archive lookup and confirmation; no public list/raw endpoint."""
from datetime import datetime,timezone
from decimal import Decimal
import hashlib
from typing import Literal

from fastapi import Depends,HTTPException,Path
from pydantic import Field,field_validator
from sqlalchemy import func,select
from sqlalchemy.orm import Session

from .admissions import Assessment,Campaign,CandidateEntry,CompetitionGroup,PublishedSnapshot,Source,SourceSnapshot,Subscription,University
from .calculation import CamelModel
from .database import BrowserSession,LookupBudget,OperationRecord
from .direction_budget import DirectionBudget,direction_budget
from .operations import remember_operation
from .source_catalog import GroupRead,group_read
from .source_tokens import Confirmation,ConfirmationError,issue,verify
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


class ConfirmInput(CamelModel):
    confirmation_token:str=Field(min_length=1,max_length=2048,repr=False)


class SubscriptionSaved(CamelModel):
    id:str
    group_id:str
    source_id:str
    created_at:datetime


class ArchiveDirection(CamelModel):
    id:str
    created_at:datetime
    group:GroupRead
    candidate:CandidateFact|None
    confirmed_snapshot_id:str|None
    notice:str|None=None


def subscription_fingerprint(group_id,candidate_key):
    return hashlib.sha256(f'archive-subscription-v1:{group_id}:{candidate_key}'.encode()).hexdigest()


def archive_direction(db,subscription,registry):
    group=db.get(CompetitionGroup,subscription.group_id);campaign=db.get(Campaign,group.campaign_id);university=db.get(University,campaign.university_id)
    first=db.scalar(select(Assessment).where(Assessment.subscription_id==subscription.id,Assessment.rules_version=='source-confirmation-v1').order_by(Assessment.assessed_at,Assessment.id).limit(1))
    confirmed=db.get(SourceSnapshot,first.snapshot_id) if first else None
    source=db.get(Source,confirmed.source_id) if confirmed else None
    if source is None:
        sources=db.scalars(select(Source).where(Source.group_id==group.id).limit(2)).all()
        source=sources[0] if len(sources)==1 else None
    meta=group_read(db,group,campaign,university,source,registry=registry)
    row=db.get(CandidateEntry,(meta.snapshot_id,subscription.candidate_key)) if meta.snapshot_id else None
    return ArchiveDirection(id=subscription.id,created_at=utc(subscription.created_at),group=meta,
                            candidate=candidate_fact(row) if row else None,confirmed_snapshot_id=confirmed.id if confirmed else None,
                            notice=None if row else 'Запись отсутствует в доступном снимке. Это не подтверждает отзыв заявления или отказ в зачислении.')


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
    @app.get('/api/v1/direction-budget',response_model=DirectionBudget)
    def budget(owner_hash:str=Depends(owner),db:Session=Depends(database)):
        return direction_budget(db,owner_hash)

    @app.get('/api/v1/subscriptions',response_model=list[ArchiveDirection])
    def subscriptions(owner_hash:str=Depends(owner),db:Session=Depends(database)):
        values=db.scalars(select(Subscription).where(Subscription.owner_hash==owner_hash).order_by(Subscription.created_at,Subscription.id).limit(21)).all()
        if len(values)>20:raise HTTPException(409,'Превышен лимит сохранённых направлений; требуется проверка данных.')
        return [archive_direction(db,value,registry) for value in values]

    @app.post('/api/v1/sources/{source_id}/lookup',response_model=LookupResult)
    def lookup(body:LookupInput,source_id:str=Path(min_length=1,max_length=36),owner_hash:str=Depends(write_owner),db:Session=Depends(database)):
        # write_owner serializes all API processes on this guest's row.
        now=clock(); budget=db.get(LookupBudget,owner_hash)
        if budget is None:
            budget=LookupBudget(owner_hash=owner_hash,window_start=now,used=0);db.add(budget)
        elapsed=(now-utc(budget.window_start)).total_seconds()
        if elapsed>=60:budget.window_start=now;budget.used=0
        if budget.used>=30:
            raise HTTPException(429,'Слишком много поисков. Подождите минуту.',headers={'Retry-After':str(max(1,60-int(elapsed)))})
        budget.used+=1;db.commit()
        if key is None:raise HTTPException(409,'Поиск источника не настроен.')
        source,binding,snapshot,group=available_source(db,source_id,registry)
        candidate_key=scoped_candidate_key(binding,body.public_code,key)
        row=db.get(CandidateEntry,(snapshot.id,candidate_key))
        if row is None:return LookupResult(group=group,found=False)
        now=clock();session=db.get(BrowserSession,owner_hash)
        expires=min(int(now.timestamp())+300,int(utc(session.expires_at).timestamp()))
        claims=Confirmation(version=1,source_id=source.id,group_id=source.group_id,snapshot_id=snapshot.id,candidate_key=candidate_key,expires=expires)
        return LookupResult(group=group,found=True,candidate=candidate_fact(row),confirmation_token=issue(claims,owner_hash,key),expires_at=datetime.fromtimestamp(expires,timezone.utc))

    @app.delete('/api/v1/subscriptions/{subscription_id}',status_code=204)
    def remove_subscription(subscription_id:str=Path(min_length=1,max_length=36),owner_hash:str=Depends(write_owner),db:Session=Depends(database)):
        value=db.scalar(select(Subscription).where(Subscription.id==subscription_id,Subscription.owner_hash==owner_hash))
        if value is None:raise HTTPException(404,'Архивная запись не найдена.')
        fingerprint=subscription_fingerprint(value.group_id,value.candidate_key)
        operations=db.scalars(select(OperationRecord).where(OperationRecord.owner_hash==owner_hash,
                            OperationRecord.key.startswith('archive-confirm:'),OperationRecord.fingerprint==fingerprint)).all()
        for operation in operations:
            operation.response=None;operation.response_status=410
        db.delete(value);db.commit()

    @app.post('/api/v1/subscriptions',response_model=SubscriptionSaved,status_code=201)
    def subscribe(body:ConfirmInput,owner_hash:str=Depends(write_owner),db:Session=Depends(database)):
        if key is None:raise HTTPException(409,'Поиск источника не настроен.')
        now=clock()
        try:claims=verify(body.confirmation_token,owner_hash,key,int(now.timestamp()),allow_expired=True)
        except ConfirmationError:raise HTTPException(403,'Сначала найдите и подтвердите запись в этой сессии.') from None
        operation_key='archive-confirm:'+hashlib.sha256(body.confirmation_token.encode()).hexdigest()
        fingerprint=subscription_fingerprint(claims.group_id,claims.candidate_key)
        cached=db.get(OperationRecord,(owner_hash,operation_key))
        if cached:
            if cached.fingerprint!=fingerprint:raise HTTPException(409,'Подтверждение уже использовано для другой операции.')
            if cached.response_status==410:raise HTTPException(410,'Это сохранение уже удалено. Повтор не восстановит запись.')
            return SubscriptionSaved.model_validate(cached.response)
        if db.scalar(select(func.count()).select_from(OperationRecord).where(OperationRecord.owner_hash==owner_hash))>=12000:
            raise HTTPException(409,'Достигнут лимит операций гостевой сессии.')
        if int(now.timestamp())>=claims.expires:raise HTTPException(410,'Срок подтверждения истёк. Найдите запись снова.')
        existing=db.scalar(select(Subscription).where(Subscription.owner_hash==owner_hash,Subscription.group_id==claims.group_id,Subscription.candidate_key==claims.candidate_key))
        if existing is None:
            source,binding,snapshot,group=available_source(db,claims.source_id,registry)
            if source.group_id!=claims.group_id or snapshot.id!=claims.snapshot_id:raise HTTPException(409,'На сервере другой снимок. Найдите запись ещё раз перед сохранением.')
            row=db.get(CandidateEntry,(snapshot.id,claims.candidate_key))
            if row is None:raise HTTPException(409,'Запись больше не подтверждена выбранным снимком.')
            if direction_budget(db,owner_hash).total>=20:raise HTTPException(409,'Можно сохранить до20 направлений всего: ручных и архивных.')
            existing=Subscription(owner_hash=owner_hash,group_id=source.group_id,candidate_key=claims.candidate_key,created_at=now)
            db.add(existing);db.flush()
            db.add(Assessment(subscription_id=existing.id,group_id=source.group_id,snapshot_id=snapshot.id,rules_version='source-confirmation-v1',assessed_at=now,state='unsupported',
                              facts=candidate_fact(row).model_dump(mode='json',by_alias=True)|{'sourceId':source.id,'dataKind':snapshot.kind},
                              assumptions=['Сохранены факты источника; официальный результат зачисления не рассчитывался.']))
        result=SubscriptionSaved(id=existing.id,group_id=existing.group_id,source_id=claims.source_id,created_at=utc(existing.created_at))
        remember_operation(db,owner_hash,operation_key,fingerprint,None,result)
        db.commit()
        return result
