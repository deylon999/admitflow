"""University, group and coverage routes on their original HTTP paths."""

from fastapi import Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.catalog import search_universities
from app.catalog.coverage import coverage
from app.catalog.national_coverage import national_coverage, with_checksum
from app.catalog.source_catalog import GroupCatalog, groups as search_groups
from app.schemas import CatalogRead, CoverageRead, SourceStatus
from app.sources.status import source_status


def install_legacy_catalog(app, database, source_registry):
    @app.get('/api/v1/universities', response_model=CatalogRead)
    def universities(q: str = Query('', max_length=120), offset: int = Query(0,ge=0,le=100000), db: Session = Depends(database)):
        return search_universities(db, q, offset)

    @app.get('/api/v1/groups',response_model=GroupCatalog)
    def groups(q:str=Query('',max_length=120),university_id:str=Query('',alias='universityId',max_length=80),
               branch_id:str=Query('',alias='branchId',max_length=80),year:int|None=Query(None,ge=2000,le=2100),
               after:str|None=Query(None,max_length=36),limit:int=Query(20,ge=1,le=50),db:Session=Depends(database)):
        return search_groups(db,q=q,university_id=university_id,branch_id=branch_id,year=year,after=after,limit=limit,registry=source_registry)

    @app.get('/api/v1/sources/{source_id}/status', response_model=SourceStatus)
    def get_source_status(source_id: str, db: Session = Depends(database)):
        result = source_status(db,source_id,registry=source_registry)
        if result is None:
            raise HTTPException(404,'Источник не найден.')
        return result

    @app.get('/api/v1/coverage', response_model=CoverageRead)
    def get_coverage(db: Session = Depends(database)):
        return coverage(db,registry=source_registry)

    @app.get('/api/v1/coverage/national')
    def get_national_coverage(db: Session = Depends(database)):
        # Aggregates only: no candidate rows, session data or raw source bodies.
        return with_checksum(national_coverage(db,registry_rules=source_registry))
