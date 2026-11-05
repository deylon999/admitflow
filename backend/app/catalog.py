"""Small, explicitly audited catalog; no implied nationwide coverage."""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from .admissions import University
from .schemas import CatalogRead, UniversityRead
from .national_catalog import load_catalog

AUDITED_AT = datetime(2026, 11, 1, tzinfo=timezone.utc)
INITIAL_UNIVERSITIES = [
    {
        'id': 'sgu-saratov',
        'name': 'СГУ имени Н. Г. Чернышевского',
        'official_url': 'https://www.sgu.ru/',
        'provenance_url': 'https://www.sgu.ru/svodka',
        'verified_at': AUDITED_AT,
    },
    {
        'id': 'sgups-novosibirsk',
        'name': 'СГУПС — Сибирский государственный университет путей сообщения',
        'official_url': 'https://www.stu.ru/',
        'provenance_url': 'https://www.stu.ru/abiturient/spiski_abiturientov/konkursnie_spiski',
        'verified_at': AUDITED_AT,
    },
]


def seed_catalog(engine):
    insert = postgres_insert if engine.dialect.name == 'postgresql' else sqlite_insert
    with Session(engine) as db:
        db.execute(insert(University).values(INITIAL_UNIVERSITIES).on_conflict_do_nothing(index_elements=['id']))
        db.commit()


def catalog_records(db):
    snapshot=load_catalog()
    records={row.id:dict(id=row.id,name=row.name if len(row.name)<=160 else row.name[:159]+'…',legal_name=row.name,
        official_url=row.official_url,provenance_url=row.provenance_url,verified_at=snapshot.captured_at,
        region=row.region,is_branch=row.is_branch,catalog_origin='monitoring',coverage='manual') for row in snapshot.institutions}
    for row in db.scalars(select(University).order_by(University.id)).all():
        metadata=records.get(row.id,{})
        records[row.id]={**metadata,'id':row.id,'name':row.name,'official_url':row.official_url,
            'provenance_url':row.provenance_url,'verified_at':row.verified_at.replace(tzinfo=timezone.utc) if row.verified_at.tzinfo is None else row.verified_at,
            'region':row.region or metadata.get('region'),'coverage':'manual','catalog_origin':'operator'}
    return list(records.values())


def catalog_size(db):
    return len(catalog_records(db))


def search_universities(db, query, offset=0):
    # Frozen reference edition, Unicode casefold, deterministic ID pagination.
    needles=query.strip().casefold().split()
    records=catalog_records(db)
    matches=[row for row in records if all(token in ' '.join(str(row.get(key) or '') for key in ('name','legal_name','region','id')).casefold() for token in needles)]
    matches.sort(key=lambda row:(row['catalog_origin']!='operator',row['id']))
    end=offset+50
    return CatalogRead(total=len(matches),items=[UniversityRead(**row) for row in matches[offset:end]],
                       next_offset=end if end<len(matches) else None,registry_total=len(load_catalog().institutions),registry_edition=load_catalog().edition)
