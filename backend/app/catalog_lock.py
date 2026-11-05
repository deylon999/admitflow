"""Serialize catalog registration, including shared university/campaign rows."""
from sqlalchemy import text


def lock_catalog(db,engine):
    if engine.dialect.name=='sqlite':db.execute(text('BEGIN IMMEDIATE'))
    else:db.execute(text("SELECT pg_advisory_xact_lock(hashtextextended('catalog-registration-v1',173))"))
