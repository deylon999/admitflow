"""Transactionally maintained read keys, with an exact source-SQL fallback.

There is no TTL or background refresh. Publications and projection changes
commit together. A different organization/archive policy uses the original SQL
path until an operator synchronizes this policy in one transaction.
"""
import argparse
import hashlib
from functools import lru_cache

from sqlalchemy import select, update

from .accreditation_registry import load_registry
from .catalog_import import REVIEWED_IDS
from .national_catalog import load_catalog
from .program_catalog_models import ProgramCatalogReadFact as ReadFact, ProgramCatalogReadScope as ReadScope


def _inputs():
    return load_catalog().institution_ids, load_registry().registry_only_ids, tuple(REVIEWED_IDS)


@lru_cache(maxsize=8)
def _fingerprint(catalog_ids,registry_ids,reserved_ids):
    # Pure function keyed by the complete immutable input values. No database
    # facts, publication state, TTL or stale-result window are cached.
    known=sorted(set(catalog_ids+registry_ids))
    reserved=sorted(reserved_ids)
    payload='known:\n'+'\n'.join(known)+'\nreserved:\n'+'\n'.join(reserved)
    return hashlib.sha256(payload.encode()).hexdigest()


def policy():
    catalog,registry,reserved=_inputs()
    return dict(scope_hash=_fingerprint(catalog,registry,reserved),
        known_ids=sorted(set(catalog+registry)),reserved_ids=sorted(reserved))


def statement(db):
    if db.get_bind().dialect.name!='postgresql':
        return None
    scope_hash=db.scalar(select(ReadScope.scope_hash).where(ReadScope.id==1))
    if not matches_policy(scope_hash):
        return None
    return fact_statement()


def matches_policy(scope_hash):
    return scope_hash == _fingerprint(*_inputs())


def fact_statement():
    return select(ReadFact.public_id.label('id'),ReadFact.program_id.label('pid'),ReadFact.revision_id.label('rid'),
        ReadFact.university_id,ReadFact.year,ReadFact.sort_text,ReadFact.search_text).where(ReadFact.eligible)


def refresh_policy(engine):
    if engine.dialect.name!='postgresql':
        raise ValueError('read_projection_requires_postgresql')
    expected=policy()
    with engine.begin() as db:
        result=db.execute(update(ReadScope).where(ReadScope.id==1).values(**expected))
        if result.rowcount!=1:
            raise ValueError('read_projection_scope_missing')
    return expected['scope_hash']


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['refresh-policy'])
    parser.parse_args()
    from app.core.config import Settings
    from app.core.database import make_engine
    engine=make_engine(Settings.from_env().database_url)
    try:
        print('Scope synchronized: '+refresh_policy(engine))
    finally:
        engine.dispose()


if __name__=='__main__':main()
