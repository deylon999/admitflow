"""Explicit, atomic metadata import. No applicants, sources or worker activation.

Run after migrations: python -m app.catalog_import
"""
from sqlalchemy.orm import Session

from .admissions import Campaign, CompetitionGroup, University
from .catalog_lock import lock_catalog
from .config import Settings
from .database import make_engine
from .sources.table_profiles import PROFILES

# Intentionally small first product slice. Each scope has an independent audit.
REVIEWED_IDS = ('sgu-2026-4588', 'sgu-2026-4576')


def reviewed_profiles():
    return tuple(PROFILES[key] for key in REVIEWED_IDS)


def expected_fields(profile):
    meta = dict(profile.catalog)
    return {
        'campaign_id': meta['campaign_id'], 'official_id': meta['official_id'],
        'title': meta['title'], 'study_form': meta['study_form'],
        'funding': meta['funding'], 'category': meta['category'], 'seats': profile.seats,
    }


def import_reviewed(engine):
    def ensure(db, model, identifier, fields, defaults=None):
        row = db.get(model, identifier)
        if row is None:
            row = model(id=identifier, **fields, **(defaults or {}))
            db.add(row)
            db.flush()
        if any(getattr(row, key) != value for key, value in fields.items()):
            raise ValueError(f'catalog_identity_conflict:{model.__tablename__}:{identifier}')

    with Session(engine) as db:
        lock_catalog(db, engine)
        for profile in reviewed_profiles():
            meta = dict(profile.catalog)
            ensure(db, University, meta['university_id'], {
                'name': meta['university_name'], 'official_url': meta['university_url'],
            }, {'provenance_url': profile.url, 'verified_at': profile.proof.verified_at})
            ensure(db, Campaign, meta['campaign_id'], {
                'university_id': meta['university_id'], 'year': profile.year, 'level': meta['level'],
            })
            ensure(db, CompetitionGroup, profile.group_id, expected_fields(profile), {'coverage': 'candidate'})
        db.commit()
    return {'importedProgramScopes': len(REVIEWED_IDS), 'sourceActivation': False}


def main():
    engine = make_engine(Settings.from_env().database_url)
    try:
        print(import_reviewed(engine))
    finally:
        engine.dispose()


if __name__ == '__main__':
    main()
