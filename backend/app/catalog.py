"""Small, explicitly audited catalog; no implied nationwide coverage."""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from .admissions import University
from .schemas import CatalogRead, UniversityRead

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


def search_universities(db, query):
    # The initial set contains two records. Python casefold keeps Russian search
    # consistent on SQLite and PostgreSQL; indexed search comes with scaling.
    needle = query.strip().casefold()
    records = db.scalars(select(University).order_by(University.id)).all()
    matches = [row for row in records if needle in row.name.casefold() or needle in row.id.casefold()]
    return CatalogRead(total=len(matches), items=[UniversityRead(
        id=row.id, name=row.name, official_url=row.official_url,
        provenance_url=row.provenance_url,
        verified_at=row.verified_at.replace(tzinfo=timezone.utc) if row.verified_at.tzinfo is None else row.verified_at,
        coverage='manual',
    ) for row in matches[:50]])
