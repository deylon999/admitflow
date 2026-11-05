"""Explicit single/batch registration from the closed reviewed manifest."""
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..admissions import University,Campaign,CompetitionGroup,Source
from ..catalog_lock import lock_catalog
from .contracts import AdapterError,SourceBinding
from .registry import PRODUCTION_REGISTRY

MAX_BATCH_PROFILES=100


def _register(db,profile,*,enable,registry):
    if type(enable) is not bool or profile.proof is None:raise AdapterError('unattested_adapter')
    meta=dict(profile.catalog)
    def record(model,identifier,fields,defaults=None):
        row=db.scalar(select(Source).where(Source.id==identifier).with_for_update()) if model is Source else db.get(model,identifier)
        created=row is None
        if created:row=model(id=identifier,**fields,**(defaults or {}));db.add(row);db.flush()
        if any(getattr(row,key)!=value for key,value in fields.items()):raise AdapterError('invalid_binding')
        return row,created
    record(University,meta['university_id'],{'name':meta['university_name'],'official_url':meta['university_url']},
           {'provenance_url':profile.url,'verified_at':profile.proof.verified_at})
    record(Campaign,meta['campaign_id'],{'university_id':meta['university_id'],'year':profile.year,'level':meta['level']})
    record(CompetitionGroup,profile.group_id,{'campaign_id':meta['campaign_id'],'official_id':meta['official_id'],'title':meta['title'],
           'study_form':meta['study_form'],'funding':meta['funding'],'category':meta['category'],'seats':profile.seats},{'coverage':'candidate'})
    source,created=record(Source,profile.source_id,{'group_id':profile.group_id,'url':profile.url,'domain':profile.url.split('/')[2],'adapter_version':profile.version,'snapshot_kind':profile.kind},{'enabled':False})
    if enable and source.last_error_code=='operator_quarantine':raise AdapterError('operator_quarantine')
    if enable:
        registry.resolve(SourceBinding(source.id,source.group_id,profile.year,source.url,source.domain,profile.version,profile.kind,True));source.enabled=True
    from ..source_operations import record as journal
    journal(db,source,'enable' if enable else 'register','created' if created else 'updated')
    return dict(sourceId=source.id,groupId=source.group_id,created=created,enabled=source.enabled,year=profile.year,kind=profile.kind,adapterVersion=profile.version)


def register_profile(engine,profile,*,enable=False,registry=PRODUCTION_REGISTRY):
    with Session(engine) as db:
        lock_catalog(db,engine)
        result=_register(db,profile,enable=enable,registry=registry)
        db.commit();return result


def select_profiles(source_ids):
    from .table_profiles import PROFILES
    if (not isinstance(source_ids,(list,tuple)) or not 1<=len(source_ids)<=MAX_BATCH_PROFILES
        or any(not isinstance(ident,str) for ident in source_ids) or len(set(source_ids))!=len(source_ids)):
        raise AdapterError('invalid_binding')
    if any(ident not in PROFILES for ident in source_ids):raise AdapterError('unsupported_source')
    return tuple(PROFILES[ident] for ident in source_ids)


def register_profiles(engine,source_ids,*,enable=False,registry=PRODUCTION_REGISTRY):
    if type(enable) is not bool:raise AdapterError('invalid_binding')
    profiles=select_profiles(source_ids)
    with Session(engine) as db:
        lock_catalog(db,engine)
        results={p.source_id:_register(db,p,enable=enable,registry=registry) for p in sorted(profiles,key=lambda p:p.source_id)}
        db.commit()
        return dict(atomic=True,items=[results[ident] for ident in source_ids],created=sum(v['created'] for v in results.values()),count=len(results))
