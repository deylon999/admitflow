"""Read facade for v3. Old catalog and tracker contracts remain independent."""
from datetime import datetime, time, timezone
import re
from typing import Literal

from fastapi import Depends, HTTPException, Query
from sqlalchemy import BigInteger, Integer, case, cast, exists, func, inspect, literal, null, select, tuple_, union_all
from sqlalchemy.orm import Session

from .admissions import Campaign, CompetitionGroup, CompetitionGroupProgram, University
from .catalog_import import REVIEWED_IDS, expected_fields, reviewed_profiles
from .accreditation_registry import SOURCE_URL as ACCREDITATION_URL, load_registry
from .national_catalog import load_catalog
from .exam_requirements import SUBJECTS, for_group
from .product_catalog_schemas import (
    Accreditation, CatalogCompetitionGroup, CatalogProgram, CatalogUniversity, ExamOption, ExamRequirements, ExamSource, ExamTest, ProgramPage,
    Provenance, UniversityPage, UniversityNameSource, BranchInfo,
)
from .university_names import choose_name
from .program_catalog_models import ProgramCatalogFact as Fact, ProgramCatalogRevision as Revision, ProgramCatalogPublication as Publication, ProgramCatalogGroupFact as GroupFact


def legacy_programs(db, *, with_program_links=True):
    """The bounded, independently reviewed archive slice retains all old values."""
    profiles = {p.group_id: p for p in reviewed_profiles()}
    institutions = {r.id: r for r in load_catalog().institutions}
    rows = db.execute(select(CompetitionGroup, Campaign, University)
                      .join(Campaign, Campaign.id == CompetitionGroup.campaign_id)
                      .join(University, University.id == Campaign.university_id)
                      .where(CompetitionGroup.id.in_(profiles))).all()
    result = []
    links = {}
    if with_program_links:
        for group_id, program_id in db.execute(select(CompetitionGroupProgram.group_id, CompetitionGroupProgram.program_id)
                                              .where(CompetitionGroupProgram.group_id.in_(profiles))):
            links.setdefault(group_id, []).append(program_id)
    for group, campaign, university in rows:
        profile = profiles[group.id]
        meta = dict(profile.catalog)
        # Operator-edited or manual rows are never silently promoted to facts.
        if (any(getattr(group, key) != value for key, value in expected_fields(profile).items())
                or (campaign.university_id, campaign.year, campaign.level)
                != (meta['university_id'], profile.year, meta['level'])
                or (university.name, university.official_url)
                != (meta['university_name'], meta['university_url'])
                or university.id not in institutions):
            continue
        code = re.match(r'^\d{2}\.\d{2}\.\d{2}\b', group.title)
        source = Provenance(url=profile.url, verified_at=profile.proof.verified_at,
                            kind='archive', original_sha256=profile.proof.original_sha256)
        linked = links.get(group.id, [])
        result.append(CatalogProgram(
            id=group.id, program_id=linked[0] if len(linked) == 1 else None,
            competition_groups=[CatalogCompetitionGroup(id=group.id, campaign_id=campaign.id,
                official_id=group.official_id, title=group.title, study_form=group.study_form,
                funding=group.funding, category=group.category, seats=group.seats, provenance=source)],
            university_id=university.id, university_name=university.name,
            region=institutions[university.id].region, campaign_id=campaign.id,
            year=campaign.year, level=campaign.level, code=code[0] if code else None,
            title=group.title, study_form=group.study_form, funding=group.funding,
            category=group.category, seats=group.seats,
            exam_requirements=exam_requirements(group, campaign, code[0] if code else None),
            provenance=source,
        ))
    return result


def program_index(db):
    """SQL projection of current verified publications plus the bounded archive.

    Identity collisions are quarantined, never resolved by title or latest date.
    Queries materialize only requested pages; no applicant/raw data is selected.
    """
    legacy = {row.id: row for row in legacy_programs(db)}
    known = [r.id for r in load_catalog().institutions] + [r.id for r in load_registry().registry_only]
    current = (select(Fact.public_id.label('id'), Fact.program_id.label('pid'), Fact.revision_id.label('rid'),
        Fact.campaign_id.label('cid'), Campaign.university_id, Campaign.year, Fact.sort_text, Fact.search_text)
        .join(Revision, Revision.id == Fact.revision_id)
        .join(Publication, Publication.revision_id == Revision.id)
        .join(Campaign, Campaign.id == Fact.campaign_id)
        .where(Revision.verification_status == 'verified', Campaign.university_id.in_(known)).cte('catalog_current'))
    # Global collision checks compare identity keys, never titles or request
    # filters. Anti joins avoid sorting wide strings for two windows.
    rival_public = current.alias('rival_public')
    rival_scope = current.alias('rival_scope')
    public_conflict = exists(select(1).select_from(rival_public).where(
        rival_public.c.id == current.c.id,
        (rival_public.c.rid != current.c.rid) | (rival_public.c.pid != current.c.pid))).correlate(current)
    scope_conflict = exists(select(1).select_from(rival_scope).where(
        rival_scope.c.pid == current.c.pid, rival_scope.c.cid == current.c.cid,
        rival_scope.c.rid != current.c.rid)).correlate(current)
    published = select(*(current.c[k] for k in ('id','pid','rid','university_id','year','sort_text','search_text'))).where(
        ~public_conflict, ~scope_conflict)
    published = published.where(current.c.id.not_in(REVIEWED_IDS))
    if legacy:
        archive = [select(literal(p.id).label('id'), literal(p.program_id).label('pid'), literal(None).label('rid'),
            literal(p.university_id).label('university_id'), literal(p.year).label('year'),
            literal(p.title.casefold()).label('sort_text'),
            literal(f'{p.title} {p.code or ""} {p.university_name}'.casefold()).label('search_text')) for p in legacy.values()]
        return union_all(published, *archive).subquery(), legacy
    return published.subquery(), legacy


def hydrate_programs(db, keys, legacy):
    """Hydrate only the selected programme page and its explicitly reviewed links."""
    selected = [(r.rid, r.pid) for r in keys if r.rid is not None]
    result = dict(legacy)
    if selected:
        groups = {}
        for value in db.scalars(select(GroupFact).where(tuple_(GroupFact.revision_id, GroupFact.program_id).in_(selected))):
            groups.setdefault((value.revision_id, value.program_id), []).append(value.facts)
        regions = {r.id:r.region for r in load_catalog().institutions}
        regions.update({r.id:r.region or 'Регион не указан' for r in load_registry().registry_only})
        for fact, revision, campaign in db.execute(select(Fact, Revision, Campaign)
                .join(Revision, Revision.id == Fact.revision_id).join(Campaign, Campaign.id == Fact.campaign_id)
                .where(tuple_(Fact.revision_id, Fact.program_id).in_(selected))):
            source = Provenance(url=revision.original_url, verified_at=revision.checked_at,
                                kind='admissions', original_sha256=revision.original_sha256)
            result[fact.public_id] = CatalogProgram(id=fact.public_id, program_id=fact.program_id,
                university_id=campaign.university_id, university_name=revision.university_name,
                region=regions[campaign.university_id], campaign_id=campaign.id, year=campaign.year, level=campaign.level,
                code=fact.code, title=fact.title, study_form=fact.study_form, funding=fact.funding,
                category=fact.category, seats=fact.seats, provenance=source,
                competition_groups=[CatalogCompetitionGroup(campaign_id=campaign.id, provenance=source,
                    **{key:g[key] for key in ('id','official_id','title','study_form','funding','category','seats')})
                    for g in sorted(groups.get((fact.revision_id, fact.program_id), []), key=lambda g:g['id'])])
    return [result[r.id] for r in keys]


def programs(db):
    """Full export for coverage and offline checks against pre-upgrade schemas."""
    schema = inspect(db.connection())
    if not schema.has_table(Publication.__tablename__):
        return legacy_programs(db, with_program_links=schema.has_table(CompetitionGroupProgram.__tablename__))
    index, legacy = program_index(db)
    result = []
    for keys in db.execute(select(index).order_by(index.c.sort_text, index.c.id)).partitions(1000):
        result.extend(hydrate_programs(db, keys, legacy))
    return result


def program_page(db, *, q='', university_id='', year=None, subject='', offset=0, limit=12, sort='name'):
    index, legacy = program_index(db)
    base = select(index).where(index.c.university_id == university_id) if university_id else select(index)
    # One statement reuses the verified/collision-checked scope for facets,
    # total and page. PostgreSQL materializes multiply referenced CTEs once.
    # Metadata rows survive empty/deep pages; no full catalogue reaches Python.
    scope = base.cte('catalog_scope')
    matches = select(scope.c.id, scope.c.pid, scope.c.rid, scope.c.sort_text)
    if year is not None:
        matches = matches.where(scope.c.year == year)
    if subject:
        matches = matches.where(literal(False))
    for token in q.casefold().split():
        matches = matches.where(scope.c.search_text.contains(token, autoescape=True))
    matches = matches.cte('catalog_matches')
    order = (matches.c.sort_text.desc(), matches.c.id.desc()) if sort == 'name-desc' else (matches.c.sort_text, matches.c.id)
    page = select(matches).order_by(*order).offset(offset).limit(limit).cte('catalog_page')
    page_order = (page.c.sort_text.desc(), page.c.id.desc()) if sort == 'name-desc' else (page.c.sort_text, page.c.id)
    records = union_all(
        select(literal('page').label('kind'), page.c.id, page.c.pid, page.c.rid,
               cast(null(), Integer).label('year'), cast(null(), BigInteger).label('total'),
               func.row_number().over(order_by=page_order).label('position')),
        select(literal('total'), null(), null(), null(), cast(null(), Integer),
               func.count(), literal(0)).select_from(matches),
        select(literal('year'), null(), null(), null(), scope.c.year,
               cast(null(), BigInteger), literal(0)).distinct(),
    ).order_by('kind', 'position')
    rows = db.execute(records).all()
    keys = [r for r in rows if r.kind == 'page']
    total = next(r.total for r in rows if r.kind == 'total')
    years = sorted((r.year for r in rows if r.kind == 'year'), reverse=True)
    return ProgramPage(items=hydrate_programs(db, keys, legacy), total=total,
                       next_offset=offset+limit if offset+limit < total else None, years=years, subjects=[])


def exam_requirements(group, campaign, code):
    rules = for_group(group.id, year=campaign.year, level=campaign.level, code=code, study_form=group.study_form) if code else None
    if rules is None:
        return None
    def tests(items):
        return [ExamTest(position=t.position, options=[ExamOption(subject=o.subject, title=SUBJECTS[o.subject], min_score=o.min_score)
                                                        for o in t.options]) for t in items]
    source = rules.source
    return ExamRequirements(
        tests=tests(rules.tests), additional_tests=None if rules.additional_tests is None else tests(rules.additional_tests),
        notes=list(rules.notes), source=ExamSource(url=source.url, title=source.title, document_date=source.document_date.isoformat(),
                                                   sha256=source.sha256, checked_at=source.checked_at, cross_check_url=source.cross_check_url))


def accreditation(org, registry, method):
    return Accreditation(status='active', ogrn=org.ogrn, inn=org.inn, certificate_number=org.certificate_number,
                         bachelor_programs=org.bachelor_programs, specialist_programs=org.specialist_programs,
                         branches_with_programs=org.branches_with_programs, departmental=org.departmental,
                         match_method=method, dataset_date=registry.dataset_date.isoformat(), source_url=ACCREDITATION_URL)


def region_key(value):
    value = ' '.join(re.sub(r'[^0-9a-zа-яё]+', ' ', (value or '').casefold().replace('ё', 'е')).split())
    value = re.sub(r'^(республика|г) ', '', value)
    return re.sub(r' \(.*', '', value).split(' ')[0] if value else ''


def display_name(org):
    """Short name from the register when it is a real name; some records hold a dash or nothing there."""
    short = (org.short_name or '').strip()
    return short if len(re.findall(r'[A-Za-zА-Яа-яЁё]', short)) >= 3 else org.name


def registry_only(snapshot, registry):
    """Domestic accredited organisations missing from the monitoring catalog, as their own records."""
    regions = {region_key(r.region): r.region for r in snapshot.institutions}
    verified = datetime.combine(registry.dataset_date, time.min, tzinfo=timezone.utc)
    return [CatalogUniversity(
        id=org.id, name=display_name(org), legal_name=org.name,
        region=regions.get(region_key(org.region), org.region or 'Регион не указан'), is_branch=False,
        official_url=org.official_url,
        provenance=Provenance(url=ACCREDITATION_URL, verified_at=verified, kind='accreditation'),
        known_program_count=0, years=[], accreditation=accreditation(org, registry, 'registry'),
    ) for org in registry.registry_only]


def with_display_names(rows, snapshot, registry):
    matched = registry.by_catalog_id
    by_id = {row.id: row for row in snapshot.institutions}
    only = {org.id: org for org in registry.registry_only}
    for row in rows:
        institution = by_id.get(row.id)
        org = matched.get(institution.registry_id) if institution else only.get(row.id)
        choice = choose_name(identifier=row.id, full_name=row.legal_name, is_branch=row.is_branch,
                             provenance=row.provenance, source_sha256=snapshot.sha256 if institution else registry.archive_sha256,
                             registry_org=org, registry=registry)
        row.display_name = choice.value
        row.display_name_source = UniversityNameSource(kind=choice.kind, url=choice.source_url, verified_at=choice.verified_at,
                                                      sha256=choice.source_sha256, rule_version=choice.rule_version)
        row.name_aliases = list(choice.aliases)
        if choice.branch_source_url:
            row.branch_info = BranchInfo(parent_university_name=choice.parent_name, city=choice.city,
                                         url=choice.branch_source_url, verified_at=choice.branch_verified_at,
                                         sha256=choice.branch_source_sha256)
    return rows


def universities(db, projection=None, *, course_tokens=(), course_matches=None):
    snapshot = load_catalog()
    registry = load_registry()
    matched = registry.by_catalog_id
    index, legacy = projection if projection is not None else program_index(db)
    by_university = {}
    token_flags = [func.max(case((index.c.search_text.contains(token, autoescape=True), 1), else_=0))
                   for token in course_tokens]
    for uid, year, count, *flags in db.execute(select(index.c.university_id, index.c.year, func.count(), *token_flags)
                                             .group_by(index.c.university_id, index.c.year)):
        stats = by_university.setdefault(uid, dict(count=0, years=[]))
        stats['count'] += count
        stats['years'].append(year)
        if course_matches is not None:
            for token, found in zip(course_tokens, flags):
                if found:
                    course_matches.setdefault(token, set()).add(uid)
    legacy_names = {p.university_id:p.university_name for p in legacy.values()}
    rows = [CatalogUniversity(
        id=row.id, name=legacy_names.get(row.id, row.name),
        legal_name=row.name, region=row.region, is_branch=row.is_branch,
        official_url=row.official_url,
        provenance=Provenance(url=row.provenance_url, verified_at=snapshot.captured_at,
                              kind='monitoring', edition=snapshot.edition),
        known_program_count=0, years=[],
        accreditation=accreditation(matched[row.registry_id], registry, matched[row.registry_id].match_method)
        if row.registry_id in matched and not row.is_branch else None,
    ) for row in snapshot.institutions] + registry_only(snapshot, registry)
    for row in rows:
        if row.id in by_university:
            row.known_program_count = by_university[row.id]['count']
            row.years = sorted(by_university[row.id]['years'], reverse=True)
    return with_display_names(rows, snapshot, registry)


def paginate(rows, offset, limit):
    end = offset + limit
    return rows[offset:end], end if end < len(rows) else None


def install(app, database):
    def catalog_database(db: Session = Depends(database)):
        # Counts, page IDs, facts and links must see one publication snapshot.
        if db.get_bind().dialect.name == 'postgresql':
            db.connection(execution_options={'isolation_level': 'REPEATABLE READ'})
        yield db

    @app.get('/api/v1/catalog/universities', response_model=UniversityPage)
    def university_list(
        q: str = Query('', max_length=120), region: str = Query('', max_length=120),
        offset: int = Query(0, ge=0, le=100000), limit: int = Query(12, ge=1, le=50),
        sort: Literal['name', 'name-desc'] = 'name', db: Session = Depends(catalog_database),
    ):
        projection = program_index(db)
        tokens = q.casefold().split()
        course_matches = {}
        rows = universities(db, projection, course_tokens=tokens, course_matches=course_matches)
        regions = sorted({row.region for row in rows})
        matches = [row for row in rows if (not region or row.region == region)
                   and all(token in f'{row.name} {row.legal_name} {row.display_name or ""} {" ".join(row.name_aliases)} {row.region} {row.id}'.casefold()
                           or row.id in course_matches.get(token, ()) for token in tokens)]
        matches.sort(key=lambda row: (row.name.casefold(), row.id), reverse=sort == 'name-desc')
        items, after = paginate(matches, offset, limit)
        return UniversityPage(items=items, total=len(matches), next_offset=after,
                              regions=regions, registry_edition=load_catalog().edition,
                              accreditation_date=load_registry().dataset_date.isoformat())

    @app.get('/api/v1/catalog/universities/{university_id}', response_model=CatalogUniversity)
    def university_detail(university_id: str, db: Session = Depends(catalog_database)):
        row = next((row for row in universities(db) if row.id == university_id), None)
        if row is None:
            raise HTTPException(404, 'Университет не найден.')
        return row

    @app.get('/api/v1/catalog/programs', response_model=ProgramPage)
    def program_list(
        q: str = Query('', max_length=120), university_id: str = Query('', alias='universityId', max_length=80),
        year: int | None = Query(None, ge=2000, le=2100), subject: str = Query('', max_length=120),
        offset: int = Query(0, ge=0, le=100000), limit: int = Query(12, ge=1, le=50),
        sort: Literal['name', 'name-desc'] = 'name', db: Session = Depends(catalog_database),
    ):
        return program_page(db, q=q, university_id=university_id, year=year, subject=subject,
                            offset=offset, limit=limit, sort=sort)

    @app.get('/api/v1/catalog/programs/{program_id}', response_model=CatalogProgram)
    def program_detail(program_id: str, db: Session = Depends(catalog_database)):
        index, legacy = program_index(db)
        keys = db.execute(select(index).where(index.c.id == program_id)).all()
        if not keys:
            raise HTTPException(404, 'Направление не найдено.')
        return hydrate_programs(db, keys, legacy)[0]
