"""Liveness, readiness and operational status routes."""

from fastapi import Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.operations.migrations import schema_heads
from app.operations.observability import system_status


def install_status_routes(app, database):
    @app.get('/api/live')
    def live():
        return {'status':'ok','version':'0.2.0'}

    @app.get('/api/health')
    @app.get('/api/ready')
    def health(db: Session = Depends(database)):
        try:
            revisions = db.execute(text('SELECT version_num FROM alembic_version')).scalars().all()
        except SQLAlchemyError:
            raise HTTPException(503,'База данных временно недоступна.') from None
        if set(revisions) != schema_heads():
            raise HTTPException(503,'База данных требует совместимой версии миграций.')
        return {'status': 'ok', 'version': '0.2.0'}

    @app.get('/api/status')
    def operational_status(db: Session = Depends(database)):
        # Aggregates only. /api/health stays independent of worker and source state.
        try:
            return system_status(db,registry=app.state.source_registry)
        except SQLAlchemyError:
            raise HTTPException(503,'База данных временно недоступна.') from None
