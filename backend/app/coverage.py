"""Reproducible DB coverage: catalog, reviewed imports and automation differ."""
from datetime import datetime, timezone
from sqlalchemy import func, select
from .admissions import Campaign,CompetitionGroup,PublishedSnapshot,Source,SourceSnapshot,University
from .sources.contracts import AdapterError
from .sources.publishing import binding_from_db,utc
from .sources.registry import PRODUCTION_REGISTRY
from .sources.status import source_status
from .catalog import catalog_size
from .national_catalog import load_catalog


def coverage(db,*,registry=PRODUCTION_REGISTRY,now=None):
    now=now or datetime.now(timezone.utc)
    result=dict(catalogUniversities=catalog_size(db),registryTotal=len(load_catalog().institutions),registryEdition=load_catalog().edition,registeredSources=db.scalar(select(func.count()).select_from(Source)),
        reviewedSources=0,importedSources=0,importedGroups=0,importedUniversities=0,importedRows=0,archiveImportedGroups=0,conditionalGroups=0,lastImportedAt=None,
        automaticSources=0,publishedGroups=0,freshGroups=0,archiveGroups=0,nationalTotal=None,generatedAt=now)
    imported={};universities=set();conditional=set();automatic={}
    for source in db.scalars(select(Source).where(Source.enabled.is_(True))).all():
        try:registry.resolve(binding_from_db(db,source))
        except AdapterError:continue
        # Count database scopes, never adapter definitions/duplicate legacy proofs.
        result['reviewedSources']+=1
        group=db.get(CompetitionGroup,source.group_id)
        policy=group.coverage=='automatic' and group.rules_version is not None
        if policy:result['automaticSources']+=1
        pointer=db.get(PublishedSnapshot,source.id)
        snapshot=db.get(SourceSnapshot,pointer.snapshot_id) if pointer else None
        if not snapshot or not snapshot.complete or not snapshot.normalized_hash or snapshot.adapter_version!=source.adapter_version:continue
        status=source_status(db,source.id,now=now,registry=registry)
        result['importedSources']+=1;result['importedRows']+=snapshot.row_count
        fetched=utc(snapshot.fetched_at)
        if result['lastImportedAt'] is None or fetched>result['lastImportedAt']:result['lastImportedAt']=fetched
        imported.setdefault(group.id,[]).append(status)
        universities.add(db.get(Campaign,group.campaign_id).university_id)
        if group.rules_version=='listed-consent-v1' and group.funding=='budget' and group.category=='general' and snapshot.seats and snapshot.seats>0:conditional.add(group.id)
        if policy:automatic.setdefault(group.id,[]).append(status)
    result.update(importedGroups=len(imported),importedUniversities=len(universities),conditionalGroups=len(conditional),
        archiveImportedGroups=sum(all(item['dataKind']=='archive' for item in states) for states in imported.values()),
        publishedGroups=len(automatic),freshGroups=sum(all(item['state']=='fresh' for item in states) for states in automatic.values()),
        archiveGroups=sum(all(item['dataKind']=='archive' for item in states) for states in automatic.values()))
    return result
