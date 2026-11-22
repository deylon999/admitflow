"""Campaign coverage of the same verified records served by the public catalogue."""
from collections import Counter, defaultdict
from dataclasses import dataclass

from sqlalchemy import and_, func, inspect, select

from app.admissions import Campaign, CompetitionGroupProgram
from app.catalog.catalog_import import REVIEWED_IDS
from app.catalog.program_catalog_import import scoped_id
from app.catalog.program_catalog_models import (
    ProgramCatalogDocument as Document, ProgramCatalogFact as Fact, ProgramCatalogGroupFact as GroupFact,
    ProgramCatalogImportAttempt as Attempt, ProgramCatalogPublication as Publication,
    ProgramCatalogReadScope as ReadScope, ProgramCatalogRevision as Revision,
)
from app.catalog.program_catalog_sources import OBSERVATIONS, load_sources
from app.catalog.product_catalog import legacy_programs, program_index, source_program_index

DEFAULT_TARGET_YEAR = 2027


def coverage_numbers(covered, total):
    return dict(coveredHeads=covered, totalHeads=total, share=round(covered / total, 4) if total else None)


@dataclass
class ScopeCounts:
    programs: int = 0
    published_programs: int = 0
    groups: int = 0
    exams: int = 0


def program_counts(db):
    """Aggregate by university, year and level before retrieving catalogue facts."""
    counts = defaultdict(ScopeCounts)
    schema = inspect(db.connection())
    if schema.has_table(Publication.__tablename__):
        index, archive = (program_index(db) if schema.has_table(ReadScope.__tablename__) else source_program_index(db))
        scope = (Campaign.year, Campaign.university_id, Campaign.level)
        facts = index.join(Fact, and_(Fact.revision_id == index.c.rid, Fact.program_id == index.c.pid))
        campaigns = facts.join(Campaign, Campaign.id == Fact.campaign_id)
        for year, uid, level, count in db.execute(select(*scope, func.count()).select_from(campaigns).group_by(*scope)):
            row = counts[year, uid, level]
            row.programs = row.published_programs = count
        archived_groups = {group.id for row in archive.values() for group in row.competition_groups}
        groups = (select(*scope, func.count(GroupFact.group_id.distinct())).select_from(campaigns)
                  .join(GroupFact, and_(GroupFact.revision_id == Fact.revision_id, GroupFact.program_id == Fact.program_id))
                  .where(GroupFact.group_id.not_in(archived_groups)).group_by(*scope))
        for year, uid, level, count in db.execute(groups):
            counts[year, uid, level].groups = count
        archive = list(archive.values())
    else:
        archive = legacy_programs(db, with_program_links=schema.has_table(CompetitionGroupProgram.__tablename__))
    archive_groups_by_scope = defaultdict(set)
    for row in archive:
        key = (row.year, row.university_id, row.level)
        counts[key].programs += 1
        counts[key].exams += row.exam_requirements is not None
        archive_groups_by_scope[key].update(g.id for g in row.competition_groups)
    for key, groups in archive_groups_by_scope.items():
        counts[key].groups += len(groups)
    return counts, archive


def _source_status(db, counts, archive, known_ids):
    sources = load_sources()
    by_id = {scoped_id('program-document', s.university_id, s.year, s.review['level'], s.review['source_namespace']): s
             for s in sources if s.review is not None}
    schema = inspect(db.connection())
    published, failures = [], []
    statuses = Counter()
    if schema.has_table(Publication.__tablename__):
        for year, university_id, level, status, count in db.execute(
                select(Campaign.year, Campaign.university_id, Campaign.level, Revision.verification_status, func.count())
                .select_from(Publication).join(Revision, Revision.id == Publication.revision_id)
                .join(Fact, Fact.revision_id == Revision.id).join(Campaign, Campaign.id == Revision.campaign_id)
                .where(Fact.public_id.not_in(REVIEWED_IDS), Campaign.university_id.in_(known_ids))
                .group_by(Campaign.year, Campaign.university_id, Campaign.level, Revision.verification_status)):
            if status == 'verified':
                public = counts.get((year, university_id, level))
                statuses[year, 'conflict'] += count - (public.published_programs if public else 0)
            else:
                statuses[year, status] += count
        for doc, rev, year, university_id in db.execute(
                select(Document, Revision, Campaign.year, Campaign.university_id)
                .select_from(Publication).join(Document, Document.id == Publication.document_id)
                .join(Revision, Revision.id == Publication.revision_id).join(Campaign, Campaign.id == Document.campaign_id)
                .order_by(Campaign.year, Campaign.university_id, Document.source_namespace)):
            published.append(dict(documentId=doc.id, revisionId=rev.id, universityId=university_id, year=year,
                namespace=doc.source_namespace, url=rev.original_url, finalUrl=rev.final_url,
                contentType=rev.content_type, documentType=rev.document_type, completeness=rev.completeness,
                publicationDate=rev.publication_date.isoformat() if rev.publication_date else None,
                fetchedAt=rev.fetched_at.isoformat(), checkedAt=rev.checked_at.isoformat(),
                originalSha256=rev.original_sha256, extractorVersion=rev.extractor_version,
                reviewSha256=rev.review_sha256, normalizedSha256=rev.normalized_sha256,
                verificationStatus=rev.verification_status))
        latest = (select(Attempt.document_id, Attempt.stage, Attempt.outcome, Attempt.error_code, Attempt.original_sha256,
                        func.row_number().over(partition_by=Attempt.document_id,
                            order_by=(Attempt.attempted_at.desc(), Attempt.id.desc())).label('position')).subquery())
        for document_id, stage, error, digest, year, university_id in db.execute(
                select(latest.c.document_id, latest.c.stage, latest.c.error_code, latest.c.original_sha256,
                       Campaign.year, Campaign.university_id).outerjoin(Document, Document.id == latest.c.document_id)
                .outerjoin(Campaign, Campaign.id == Document.campaign_id)
                .where(latest.c.position == 1, latest.c.outcome == 'rejected').order_by(latest.c.document_id)):
            source = by_id.get(document_id)
            if error and error.endswith(('_identity_conflict', '_identity_ambiguous')):
                diagnostic = 'identity_conflict'
            else:
                diagnostic = 'rejected'
            failures.append(dict(documentId=document_id, stage=stage, error=error, originalSha256=digest,
                diagnostic=diagnostic,
                year=year if year is not None else source.year if source else None,
                universityId=university_id or (source.university_id if source else None),
                url=source.url if source else None))
    archive = {(r.year, r.university_id, r.provenance.url, r.provenance.original_sha256,
                r.provenance.verified_at.isoformat()) for r in archive}
    observations = {item.key: item for item in OBSERVATIONS}
    candidates = []
    for source in sources:
        if source.review is not None:
            continue
        item = observations.get(source.key)
        candidates.append(dict(key=source.key, year=source.year, universityId=source.university_id, url=source.url,
            observation=dict(fetchedAt=item.fetched_at, originalSha256=item.sha256, status=item.status, note=item.note)
            if item else None))
    return dict(documents=published, archiveSources=[dict(year=y, universityId=u, url=url, originalSha256=sha,
                    checkedAt=at) for y, u, url, sha, at in sorted(archive)], failedSources=failures,
                awaitingReview=candidates), statuses


def programme_coverage(db, counts, archive, *, target_year, heads, to_ogrn, branch_ids, head_regions, known_ids):
    sources, statuses = _source_status(db, counts, archive, known_ids)
    by_year = defaultdict(list)
    for (year, uid, level), row in counts.items():
        by_year[year].append((uid, level, row))

    def summarize(rows):
        head_rows = [(uid, row) for uid, _, row in rows if uid in to_ogrn]
        branches = [(uid, row) for uid, _, row in rows if uid in branch_ids]
        covered = {to_ogrn[uid] for uid, _ in head_rows}
        metrics = coverage_numbers(len(covered), len(heads))
        # Neither a legacy profile nor a partial document proves that other
        # programmes of the same organisation have been collected.
        return metrics | dict(programs=sum(row.programs for _, row in head_rows),
            competitionGroups=sum(row.groups for _, row in head_rows),
            headsWithPartialProgrammes=len(covered), headsWithoutVerifiedProgrammes=len(heads) - len(covered),
            branches=dict(coveredBranches=len({uid for uid, _ in branches}),
                          programs=sum(row.programs for _, row in branches), competitionGroups=sum(row.groups for _, row in branches)),
            unmappedPrograms=sum(row.programs for uid, _, row in rows if uid not in to_ogrn and uid not in branch_ids))

    target_rows = by_year.get(target_year, ())
    target = summarize(target_rows)
    required = (3 * len(heads) + 4) // 5
    target.update(year=target_year, requiredHeads=required,
        targetMet=bool(heads) and target['coveredHeads'] >= required,
        headsNeeded=max(0, required - target['coveredHeads']),
        sourceErrors=sum(failure['year'] == target_year for failure in sources['failedSources']),
        conflictingRecords=statuses[target_year, 'conflict'], unverifiedRecords=statuses[target_year, 'unverified'],
        unreviewedSources=sum(source['year'] == target_year for source in sources['awaitingReview']))
    target_heads = defaultdict(set)
    for uid, level, _ in target_rows:
        if uid in to_ogrn:
            target_heads[level].add(to_ogrn[uid])
    covered = set().union(*target_heads.values())
    target['headsWithObservedPendingPublication'] = len({to_ogrn[source['universityId']]
        for source in sources['awaitingReview'] if source['year'] == target_year and source['universityId'] in to_ogrn
        and source['observation'] and source['observation']['status'] == 'publication_pending'} - covered)
    regions = defaultdict(set)
    for ogrn, region in head_regions.items():
        regions[region].add(ogrn)
    target['regions'] = [dict(region=region, **coverage_numbers(len(ogrns & covered), len(ogrns)))
                         for region, ogrns in sorted(regions.items())]
    target['levels'] = [dict(level=level, **coverage_numbers(len(target_heads[level] & ogrns), len(ogrns)),
                             programs=sum(row.programs for uid, tracked_level, row in target_rows
                                          if tracked_level == level and uid in to_ogrn),
                             competitionGroups=sum(row.groups for uid, tracked_level, row in target_rows
                                                   if tracked_level == level and uid in to_ogrn))
                        for level, ogrns in (
                            ('bachelor', {o.ogrn for o in heads.values() if o.bachelor_programs}),
                            ('specialist', {o.ogrn for o in heads.values() if o.specialist_programs}))]
    historical = [dict(year=year, **summarize(rows)) for year, rows in sorted(by_year.items(), reverse=True) if year < target_year]
    return dict(targetCampaign=target, historicalCampaigns=historical,
        historicalTotal=summarize([row for year, rows in by_year.items() if year < target_year for row in rows]),
        laterCampaigns=[dict(year=year, **summarize(rows)) for year, rows in sorted(by_year.items()) if year > target_year],
        sources=sources)
