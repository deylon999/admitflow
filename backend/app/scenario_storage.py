"""Append immutable scenario versions within publication/confirmation transactions."""
from sqlalchemy import select
from .admissions import Assessment,Campaign,CandidateEntry,CompetitionGroup,Source,SourceSnapshot,Subscription
from .scenarios import VERSION,assess,ScenarioResult,ASSUMPTIONS


def candidate_values(row):
    if row is None:return None
    return {'rowRef':row.row_ref,'officialRank':row.official_rank,'score':str(row.score) if row.score is not None else None,'consent':row.consent,'priority':row.priority,'participation':row.participation}


def difference(before,after):
    fields={'officialRank','score','consent','priority','participation'}
    old=before.get('candidate') or {};new=after.get('candidate') or {}
    changes=[{'field':field,'before':old.get(field),'after':new.get(field)} for field in sorted(fields) if old.get(field)!=new.get(field)]
    if bool(before.get('candidate'))!=bool(after.get('candidate')):changes.append({'field':'present','before':bool(before.get('candidate')),'after':bool(after.get('candidate'))})
    old_result,new_result=before['result'],after['result']
    for field in ('currentLower','currentUpper','allConsentPlace','seats','consentYesAbove','consentNoAbove','consentUnknownAbove','withdrawnAbove'):
        a=(old_result.get('numbers') or {}).get(field);b=(new_result.get('numbers') or {}).get(field)
        if a!=b:changes.append({'field':field,'before':a,'after':b})
    if old_result['state']!=new_result['state']:changes.append({'field':'state','before':old_result['state'],'after':new_result['state']})
    if old_result['modelVersion']!=new_result['modelVersion']:changes.append({'field':'modelVersion','before':old_result['modelVersion'],'after':new_result['modelVersion']})
    return changes


def append_one(db,subscription,snapshot,*,previous=None,rows=None,at=None):
    group=db.get(CompetitionGroup,subscription.group_id)
    if group.rules_version!=VERSION:return None
    existing=db.scalar(select(Assessment).where(Assessment.subscription_id==subscription.id,Assessment.snapshot_id==snapshot.id,Assessment.rules_version==VERSION))
    if existing is not None:return existing
    if rows is None:rows=db.scalars(select(CandidateEntry).where(CandidateEntry.snapshot_id==snapshot.id).order_by(CandidateEntry.official_rank)).all()
    row=next((r for r in rows if r.candidate_key==subscription.candidate_key),None)
    result=assess(rows,subscription.candidate_key,funding=group.funding,category=group.category,seats=snapshot.seats)
    if not snapshot.complete or not snapshot.normalized_hash or len(rows)!=snapshot.row_count:
        result=ScenarioResult(state='insufficient_data',reason_codes=['incomplete_snapshot'],assumptions=list(ASSUMPTIONS))
    facts={'result':result.model_dump(mode='json',by_alias=True),'candidate':candidate_values(row),'sourceId':snapshot.source_id,'dataKind':snapshot.kind,'funding':group.funding,'category':group.category,'diff':[]}
    old=db.scalar(select(Assessment).where(Assessment.subscription_id==subscription.id,Assessment.snapshot_id==previous.id,Assessment.rules_version==VERSION)) if previous and previous.id!=snapshot.id else None
    if old is not None:facts['diff']=difference(old.facts,facts)
    if at is None:
        from .source_history import assessment_clock
        at=assessment_clock()
    value=Assessment(subscription_id=subscription.id,group_id=group.id,snapshot_id=snapshot.id,rules_version=VERSION,assessed_at=at,state=result.state,facts=facts,assumptions=result.assumptions)
    db.add(value);return value


def append_source(db,snapshot,*,previous=None):
    group=db.get(CompetitionGroup,snapshot.group_id)
    if group.rules_version!=VERSION:return
    confirmed=select(Assessment.subscription_id).join(SourceSnapshot,Assessment.snapshot_id==SourceSnapshot.id).where(Assessment.rules_version=='source-confirmation-v1',SourceSnapshot.source_id==snapshot.source_id)
    subscriptions=db.scalars(select(Subscription).where(Subscription.id.in_(confirmed)).with_for_update()).all()
    if not subscriptions:return
    rows=db.scalars(select(CandidateEntry).where(CandidateEntry.snapshot_id==snapshot.id).order_by(CandidateEntry.official_rank)).all()
    for subscription in subscriptions:append_one(db,subscription,snapshot,previous=previous,rows=rows)


def enable_scenarios(engine,source_id,*,registry):
    from .sources.contracts import AdapterError
    from .sources.publishing import lock_source,binding_from_db
    from .sources.table_profiles import PROFILES
    from sqlalchemy.orm import Session
    profile=PROFILES.get(source_id)
    if profile is None:raise AdapterError('unsupported_source')
    with Session(engine) as db:
        source=lock_source(db,engine,source_id)
        registry.resolve(binding_from_db(db,source))
        group=db.get(CompetitionGroup,source.group_id)
        meta=dict(profile.catalog)
        campaign=db.get(Campaign,group.campaign_id)
        if (group.id!=profile.group_id or group.campaign_id!=meta['campaign_id'] or campaign.university_id!=meta['university_id'] or campaign.year!=profile.year
                or any(getattr(group,key)!=meta[key] for key in ('funding','category','study_form','official_id'))):raise AdapterError('invalid_binding')
        if group.rules_version not in (None,VERSION):raise AdapterError('invalid_binding')
        group.rules_version=VERSION
        from .admissions import PublishedSnapshot
        pointer=db.get(PublishedSnapshot,source_id)
        if pointer:append_source(db,db.get(SourceSnapshot,pointer.snapshot_id))
        db.commit();return {'sourceId':source_id,'rulesVersion':VERSION,'numericScope':'conditional listed-consent scenario only','officialResultAvailable':False}
