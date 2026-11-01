"""Catalog size and verified automation are separate metrics."""
from datetime import datetime, timezone

from sqlalchemy import func, select

from .admissions import CompetitionGroup, PublishedSnapshot, Source, SourceSnapshot, University
from .sources.contracts import AdapterError
from .sources.publishing import binding_from_db
from .sources.registry import PRODUCTION_REGISTRY
from .sources.status import source_status


def coverage(db,*,registry=PRODUCTION_REGISTRY,now=None):
    now=now or datetime.now(timezone.utc)
    result=dict(catalogUniversities=db.scalar(select(func.count()).select_from(University)),automaticSources=0,publishedGroups=0,freshGroups=0,archiveGroups=0,nationalTotal=None,generatedAt=now)
    versions=registry.attested_versions
    if not versions:
        return result
    sources=db.scalars(select(Source).join(CompetitionGroup).where(Source.enabled.is_(True),Source.adapter_version.in_(versions),CompetitionGroup.coverage=='automatic',CompetitionGroup.rules_version.is_not(None))).all()
    groups={}
    for source in sources:
        try:
            registry.resolve(binding_from_db(db,source))
        except AdapterError:
            continue
        result['automaticSources']+=1
        pointer=db.get(PublishedSnapshot,source.id)
        snapshot=db.get(SourceSnapshot,pointer.snapshot_id) if pointer else None
        if not snapshot or not snapshot.complete or not snapshot.normalized_hash or snapshot.adapter_version!=source.adapter_version:
            continue
        groups.setdefault(source.group_id,[]).append(source_status(db,source.id,now=now,registry=registry))
    result['publishedGroups']=len(groups)
    result['freshGroups']=sum(all(item['state']=='fresh' for item in states) for states in groups.values())
    result['archiveGroups']=sum(all(item['dataKind']=='archive' for item in states) for states in groups.values())
    return result
