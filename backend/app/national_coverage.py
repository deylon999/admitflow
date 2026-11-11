"""National coverage report for operators (KAN-221).

Four layers are measured separately against one denominator, the head
organisations of the accreditation register: presence in the reference
catalog, verified programmes, confirmed examination requirements and imported
competition lists. Branches are never counted as head organisations. Every
number comes from the shipped artifacts or the database; nothing is estimated.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from .accreditation_registry import SOURCE_URL as REGISTRY_URL, load_registry
from .admissions import Campaign, CompetitionGroup, PublishedSnapshot, Source, SourceSnapshot, University
from .national_catalog import load_catalog
from .observability import system_status
from .product_catalog import programs, region_key
from .sources.publishing import utc
from .sources.registry import PRODUCTION_REGISTRY
from .sources.status import source_status

TARGET = 0.6
PROBLEM_STATES = ('source_error', 'quarantined', 'stale')


def share(covered, total):
    return round(covered / total, 4) if total else None


def layer(key, title, covered, total, note):
    value = share(covered, total)
    return dict(id=key, title=title, covered=covered, total=total, share=value,
                targetMet=value is not None and value >= TARGET, note=note)


def head_ogrn_by_university(registry, catalog):
    """Catalog university id -> OGRN of a head organisation; branches map to nothing."""
    matched = registry.by_catalog_id
    result = {}
    for row in catalog.institutions:
        if not row.is_branch and row.registry_id in matched:
            result[row.id] = matched[row.registry_id].ogrn
    for org in registry.registry_only:
        result[org.id] = org.ogrn
    return result


def imported_lists(db, registry):
    """University ids with a complete published snapshot, and the per-group freshness."""
    universities, states = set(), []
    for source in db.scalars(select(Source).where(Source.enabled.is_(True)).order_by(Source.id)).all():
        pointer = db.get(PublishedSnapshot, source.id)
        snapshot = db.get(SourceSnapshot, pointer.snapshot_id) if pointer else None
        if not snapshot or not snapshot.complete:
            continue
        group = db.get(CompetitionGroup, source.group_id)
        campaign = db.get(Campaign, group.campaign_id)
        universities.add(campaign.university_id)
        status = source_status(db, source.id, registry=registry)
        states.append((campaign.year, status['state'] if status else 'unknown', status['dataKind'] if status else None))
    return universities, states


def sources_report(db, registry, now):
    counts, problems = Counter(), []
    for source in db.scalars(select(Source).order_by(Source.id)).all():
        status = source_status(db, source.id, now=now, registry=registry)
        state = status['state'] if status else 'unknown'
        counts[state] += 1
        if state in PROBLEM_STATES:
            group = db.get(CompetitionGroup, source.group_id)
            university = db.get(University, db.get(Campaign, group.campaign_id).university_id)
            problems.append(dict(sourceId=source.id, university=university.name, group=group.title, state=state,
                                 domain=source.domain, lastCheckedAt=status.get('lastCheckedAt')))
    return dict(total=sum(counts.values()), byState=dict(sorted(counts.items())), problems=problems)


def national_coverage(db, *, now=None, registry_rules=PRODUCTION_REGISTRY):
    now = now or datetime.now(timezone.utc)
    registry, catalog = load_registry(), load_catalog()
    heads = {o.ogrn: o for o in registry.organisations if not o.abroad}
    to_ogrn = head_ogrn_by_university(registry, catalog)
    catalog_region = {r.registry_id: r.region for r in catalog.institutions}

    verified = programs(db)
    program_heads, branch_programs, by_year = set(), 0, {}
    for program in verified:
        ogrn = to_ogrn.get(program.university_id)
        if ogrn is None:
            branch_programs += 1
            continue
        program_heads.add(ogrn)
        by_year.setdefault(program.year, dict(programs=set(), exams=set()))['programs'].add(ogrn)
        if program.exam_requirements is not None:
            by_year[program.year]['exams'].add(ogrn)
    exam_heads = set().union(*(v['exams'] for v in by_year.values())) if by_year else set()

    list_universities, list_states = imported_lists(db, registry_rules)
    list_heads = {to_ogrn[u] for u in list_universities if u in to_ogrn}
    fresh_groups = sum(state == 'fresh' for _, state, _ in list_states)

    total = registry.denominator
    catalog_heads = sum(1 for o in heads.values() if o.catalog_registry_id)
    layers = [
        layer('registry', 'Вуз есть в опорном каталоге', catalog_heads, total,
              'Сопоставление каталога MICCEDU с реестром аккредитации. Записи только из реестра не засчитываются.'),
        layer('programs', 'Есть проверенные программы', len(program_heads), total,
              'Хотя бы одна программа с официальным источником и проверкой. Архивные кампании засчитываются по своему году.'),
        layer('examRequirements', 'Есть подтверждённые требования ЕГЭ', len(exam_heads), total,
              'Перечень испытаний и минимальные баллы из официального документа вуза, сверенные с его текстом. Только для проверенных программ.'),
        layer('competitionLists', 'Импортирован конкурсный список', len(list_heads), total,
              'Есть опубликованный полный снимок хотя бы одного конкурса. Свежесть показана отдельно.'),
    ]

    regions = {}
    for org in heads.values():
        region = catalog_region.get(org.catalog_registry_id) or org.region or 'Регион не указан'
        row = regions.setdefault(region_key(region) or region, dict(region=region, total=0, catalog=0, programs=0, lists=0))
        row['total'] += 1
        row['catalog'] += bool(org.catalog_registry_id)
        row['programs'] += org.ogrn in program_heads
        row['lists'] += org.ogrn in list_heads

    return dict(
        generatedAt=now.isoformat(), target=TARGET,
        denominator=dict(total=total, civil=total - registry.departmental, departmental=registry.departmental,
                         abroadExcluded=sum(o.abroad for o in registry.organisations), datasetDate=registry.dataset_date.isoformat(),
                         sourceUrl=REGISTRY_URL, archiveSha256=registry.archive_sha256,
                         rule='Головная организация с действующей аккредитацией бакалавриата или специалитета; филиалы считаются вместе с ней.'),
        layers=layers,
        byYear=[dict(year=year, programs=len(v['programs']), examRequirements=len(v['exams']))
                for year, v in sorted(by_year.items(), reverse=True)],
        gaps=dict(unmatchedCatalogHeads=len(registry.unmatched_catalog_heads),
                  ambiguousCatalogHeads=sum(len(v) for v in registry.ambiguous.values()),
                  registryOnly=len(registry.registry_only), branchProgramsNotCounted=branch_programs,
                  headsWithoutPrograms=total - len(program_heads)),
        lists=dict(groups=len(list_states), freshGroups=fresh_groups,
                   archiveGroups=sum(kind == 'archive' for _, _, kind in list_states)),
        regions=sorted(regions.values(), key=lambda r: (-r['total'], r['region'])),
        sources=sources_report(db, registry_rules, now),
        operations=system_status(db, now=now, registry=registry_rules),
        inputs=dict(registrySha256=registry.sha256, catalogSha256=catalog.sha256, catalogEdition=catalog.edition,
                    verifiedPrograms=len(verified), checksum=None),
    )


def with_checksum(report):
    """Checksum over everything except times, so equal inputs give an equal checksum."""
    stable = {k: v for k, v in report.items() if k not in ('generatedAt', 'operations')}
    stable['sources'] = {k: v for k, v in report['sources'].items() if k != 'problems'}
    body = json.dumps(stable, sort_keys=True, ensure_ascii=False).encode()
    report['inputs']['checksum'] = hashlib.sha256(body).hexdigest()
    return report


def main(argv=None):
    from .config import Settings
    from .database import make_engine
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', help='Write the JSON report to this file instead of stdout')
    args = parser.parse_args(argv)
    engine = make_engine(Settings.from_env().database_url)
    try:
        with Session(engine) as db:
            report = with_checksum(national_coverage(db))
    finally:
        engine.dispose()
    body = json.dumps(report, ensure_ascii=False, indent=2, default=str) + '\n'
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as sink:
            sink.write(body)
    else:
        print(body, end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
