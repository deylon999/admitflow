"""Read facade for v3. Old catalog and tracker contracts remain independent."""
from datetime import datetime, time, timezone
import re
from typing import Literal

from fastapi import Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from .admissions import Campaign, CompetitionGroup, University
from .catalog_import import expected_fields, reviewed_profiles
from .accreditation_registry import SOURCE_URL as ACCREDITATION_URL, load_registry
from .national_catalog import load_catalog
from .product_catalog_schemas import (
    Accreditation, CatalogProgram, CatalogUniversity, ProgramPage, Provenance, UniversityPage,
)


def programs(db):
    profiles = {p.group_id: p for p in reviewed_profiles()}
    institutions = {r.id: r for r in load_catalog().institutions}
    rows = db.execute(select(CompetitionGroup, Campaign, University)
                      .join(Campaign, Campaign.id == CompetitionGroup.campaign_id)
                      .join(University, University.id == Campaign.university_id)
                      .where(CompetitionGroup.id.in_(profiles))).all()
    result = []
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
        result.append(CatalogProgram(
            id=group.id, university_id=university.id, university_name=university.name,
            region=institutions[university.id].region, campaign_id=campaign.id,
            year=campaign.year, level=campaign.level, code=code[0] if code else None,
            title=group.title, study_form=group.study_form, funding=group.funding,
            category=group.category, seats=group.seats,
            provenance=Provenance(url=profile.url, verified_at=profile.proof.verified_at,
                                  kind='archive', original_sha256=profile.proof.original_sha256),
        ))
    return result


def accreditation(org, registry, method):
    return Accreditation(status='active', ogrn=org.ogrn, inn=org.inn, certificate_number=org.certificate_number,
                         bachelor_programs=org.bachelor_programs, specialist_programs=org.specialist_programs,
                         branches_with_programs=org.branches_with_programs, departmental=org.departmental,
                         match_method=method, dataset_date=registry.dataset_date.isoformat(), source_url=ACCREDITATION_URL)


def region_key(value):
    value = ' '.join(re.sub(r'[^0-9a-zа-яё]+', ' ', (value or '').casefold().replace('ё', 'е')).split())
    value = re.sub(r'^(республика|г) ', '', value)
    return re.sub(r' \(.*', '', value).split(' ')[0] if value else ''


def registry_only(snapshot, registry):
    """Domestic accredited organisations missing from the monitoring catalog, as their own records."""
    regions = {region_key(r.region): r.region for r in snapshot.institutions}
    verified = datetime.combine(registry.dataset_date, time.min, tzinfo=timezone.utc)
    return [CatalogUniversity(
        id=org.id, name=org.short_name or org.name, legal_name=org.name,
        region=regions.get(region_key(org.region), org.region or 'Регион не указан'), is_branch=False,
        official_url=org.official_url,
        provenance=Provenance(url=ACCREDITATION_URL, verified_at=verified, kind='accreditation'),
        known_program_count=0, years=[], accreditation=accreditation(org, registry, 'registry'),
    ) for org in registry.registry_only]


def universities(db):
    snapshot = load_catalog()
    registry = load_registry()
    matched = registry.by_catalog_id
    by_university = {}
    for program in programs(db):
        by_university.setdefault(program.university_id, []).append(program)
    return [CatalogUniversity(
        id=row.id, name=by_university[row.id][0].university_name if row.id in by_university else row.name,
        legal_name=row.name, region=row.region, is_branch=row.is_branch,
        official_url=row.official_url,
        provenance=Provenance(url=row.provenance_url, verified_at=snapshot.captured_at,
                              kind='monitoring', edition=snapshot.edition),
        known_program_count=len(by_university.get(row.id, [])),
        years=sorted({p.year for p in by_university.get(row.id, [])}, reverse=True),
        accreditation=accreditation(matched[row.registry_id], registry, matched[row.registry_id].match_method)
        if row.registry_id in matched and not row.is_branch else None,
    ) for row in snapshot.institutions] + registry_only(snapshot, registry)


def paginate(rows, offset, limit):
    end = offset + limit
    return rows[offset:end], end if end < len(rows) else None


def install(app, database):
    @app.get('/api/v1/catalog/universities', response_model=UniversityPage)
    def university_list(
        q: str = Query('', max_length=120), region: str = Query('', max_length=120),
        offset: int = Query(0, ge=0, le=100000), limit: int = Query(12, ge=1, le=50),
        sort: Literal['name', 'name-desc'] = 'name', db: Session = Depends(database),
    ):
        rows = universities(db)
        regions = sorted({row.region for row in rows})
        tokens = q.casefold().split()
        course_text = {}
        if tokens:
            for program in programs(db):
                course_text[program.university_id] = course_text.get(program.university_id, '') + ' ' + program.title
        matches = [row for row in rows if (not region or row.region == region)
                   and all(token in f'{row.name} {row.legal_name} {row.region} {row.id} {course_text.get(row.id, "")}'.casefold() for token in tokens)]
        matches.sort(key=lambda row: (row.name.casefold(), row.id), reverse=sort == 'name-desc')
        items, after = paginate(matches, offset, limit)
        return UniversityPage(items=items, total=len(matches), next_offset=after,
                              regions=regions, registry_edition=load_catalog().edition,
                              accreditation_date=load_registry().dataset_date.isoformat())

    @app.get('/api/v1/catalog/universities/{university_id}', response_model=CatalogUniversity)
    def university_detail(university_id: str, db: Session = Depends(database)):
        row = next((row for row in universities(db) if row.id == university_id), None)
        if row is None:
            raise HTTPException(404, 'Университет не найден.')
        return row

    @app.get('/api/v1/catalog/programs', response_model=ProgramPage)
    def program_list(
        q: str = Query('', max_length=120), university_id: str = Query('', alias='universityId', max_length=80),
        year: int | None = Query(None, ge=2000, le=2100), subject: str = Query('', max_length=120),
        offset: int = Query(0, ge=0, le=100000), limit: int = Query(12, ge=1, le=50),
        sort: Literal['name', 'name-desc'] = 'name', db: Session = Depends(database),
    ):
        rows = [row for row in programs(db) if not university_id or row.university_id == university_id]
        years = sorted({row.year for row in rows}, reverse=True)
        tokens = q.casefold().split()
        matches = [row for row in rows if (year is None or row.year == year) and not subject
                   and all(token in f'{row.title} {row.code or ""} {row.university_name}'.casefold() for token in tokens)]
        matches.sort(key=lambda row: (row.title.casefold(), row.id), reverse=sort == 'name-desc')
        items, after = paginate(matches, offset, limit)
        return ProgramPage(items=items, total=len(matches), next_offset=after, years=years, subjects=[])

    @app.get('/api/v1/catalog/programs/{program_id}', response_model=CatalogProgram)
    def program_detail(program_id: str, db: Session = Depends(database)):
        row = next((row for row in programs(db) if row.id == program_id), None)
        if row is None:
            raise HTTPException(404, 'Направление не найдено.')
        return row
