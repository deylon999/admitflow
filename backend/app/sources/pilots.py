"""Explicit operator registration of one reviewed archive; no user URL input."""
from dataclasses import replace

from sqlalchemy import select,text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from ..admissions import Campaign,CompetitionGroup,Source,University
from ..catalog import INITIAL_UNIVERSITIES
from .adapters.sgu2026 import GROUP_ID,SOURCE_ID,URL,VERSION
from .contracts import AdapterError
from .publishing import binding_from_db
from .registry import PRODUCTION_REGISTRY

CAMPAIGN_ID='sgu-2026-bachelor'
GROUP_FIELDS=dict(campaign_id=CAMPAIGN_ID,official_id='4588',title='09.03.04 Программная инженерия — общий конкурс',
                  study_form='full-time',funding='budget',category='general',seats=16)
SOURCE_FIELDS=dict(group_id=GROUP_ID,url=URL,domain='www.sgu.ru',adapter_version=VERSION,snapshot_kind='archive')


def register_sgu(engine,*,enable=False,registry=PRODUCTION_REGISTRY):
    if type(enable) is not bool:raise ValueError('invalid_enable_flag')
    insert=pg_insert if engine.dialect.name=='postgresql' else sqlite_insert
    with Session(engine) as db:
        if engine.dialect.name=='sqlite':db.execute(text('BEGIN IMMEDIATE'))
        else:db.execute(text("SELECT pg_advisory_xact_lock(hashtextextended('pilot:sgu2026',173))"))
        db.execute(insert(University).values(INITIAL_UNIVERSITIES).on_conflict_do_nothing(index_elements=['id']))
        campaign=db.get(Campaign,CAMPAIGN_ID)
        if campaign is None:
            campaign=Campaign(id=CAMPAIGN_ID,university_id='sgu-saratov',year=2026,level='bachelor');db.add(campaign);db.flush()
        if (campaign.university_id,campaign.year,campaign.level)!=('sgu-saratov',2026,'bachelor'):raise AdapterError('invalid_binding')
        group=db.get(CompetitionGroup,GROUP_ID)
        if group is None:
            group=CompetitionGroup(id=GROUP_ID,coverage='candidate',**GROUP_FIELDS);db.add(group);db.flush()
        if any(getattr(group,key)!=value for key,value in GROUP_FIELDS.items()):raise AdapterError('invalid_binding')
        source=db.scalar(select(Source).where(Source.id==SOURCE_ID).with_for_update())
        created=source is None
        if source is None:
            source=Source(id=SOURCE_ID,enabled=False,**SOURCE_FIELDS);db.add(source);db.flush()
        if any(getattr(source,key)!=value for key,value in SOURCE_FIELDS.items()):raise AdapterError('invalid_binding')
        if enable and source.last_error_code=='operator_quarantine':raise AdapterError('operator_quarantine')
        if enable:
            registry.resolve(replace(binding_from_db(db,source),enabled=True))
            source.enabled=True
        result=dict(sourceId=SOURCE_ID,groupId=GROUP_ID,created=created,enabled=source.enabled,kind='archive',year=2026)
        from ..source_operations import record
        record(db,source,'enable' if enable else 'register','created' if created else 'updated')
        db.commit()
        return result
