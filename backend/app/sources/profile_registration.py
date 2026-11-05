"""Explicit registration from closed reviewed JSON;no arbitrary URL acceptance."""
from dataclasses import replace
from sqlalchemy import select,text
from sqlalchemy.orm import Session
from ..admissions import University,Campaign,CompetitionGroup,Source
from .contracts import AdapterError,SourceBinding
from .registry import PRODUCTION_REGISTRY
from .table_family import VERSION


def register_profile(engine,profile,*,enable=False,registry=PRODUCTION_REGISTRY):
    if type(enable) is not bool or profile.proof is None:raise AdapterError('unattested_adapter')
    meta=dict(profile.catalog)
    with Session(engine) as db:
        if engine.dialect.name=='sqlite':db.execute(text('BEGIN IMMEDIATE'))
        else:db.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:key,173))'),{'key':'reviewed-profile:'+profile.source_id})
        def record(model,identifier,fields,defaults=None):
            row=db.get(model,identifier)
            if row is None:row=model(id=identifier,**fields,**(defaults or {}));db.add(row);db.flush()
            if any(getattr(row,key)!=value for key,value in fields.items()):raise AdapterError('invalid_binding')
            return row
        record(University,meta['university_id'],{'name':meta['university_name'],'official_url':meta['university_url']},
               {'provenance_url':profile.url,'verified_at':profile.proof.verified_at})
        record(Campaign,meta['campaign_id'],{'university_id':meta['university_id'],'year':profile.year,'level':meta['level']})
        record(CompetitionGroup,profile.group_id,{'campaign_id':meta['campaign_id'],'official_id':meta['official_id'],'title':meta['title'],
               'study_form':meta['study_form'],'funding':meta['funding'],'category':meta['category'],'seats':profile.seats},{'coverage':'candidate'})
        created=db.get(Source,profile.source_id) is None
        source=record(Source,profile.source_id,{'group_id':profile.group_id,'url':profile.url,'domain':profile.url.split('/')[2],'adapter_version':profile.version,'snapshot_kind':profile.kind},{'enabled':False})
        if enable and source.last_error_code=='operator_quarantine':raise AdapterError('operator_quarantine')
        if enable:
            registry.resolve(SourceBinding(source.id,source.group_id,profile.year,source.url,source.domain,profile.version,profile.kind,True));source.enabled=True
        result={'sourceId':source.id,'groupId':source.group_id,'created':created,'enabled':source.enabled,'year':profile.year,'kind':profile.kind,'adapterVersion':profile.version}
        from ..source_operations import record
        record(db,source,'enable' if enable else 'register','created' if created else 'updated')
        db.commit();return result
