import asyncio
import logging
from contextlib import asynccontextmanager
from contextlib import suppress
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import TimeoutError as SQLAlchemyTimeoutError
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import Settings
from app.operations.maintenance import cleanup_expired_accounts, cleanup_expired_sessions
from .catalog import seed_catalog
from .catalog.api import install_legacy_catalog
from app.operations.api import install_status_routes
from app.operations.migrations import ensure_restore_complete, upgrade_schema
from app.core.http import RequestBudgetMiddleware, RequestDiagnosticsMiddleware, permitted_origin
from .core.database import make_engine
from .core.time import utc as utc
from .schemas import ValidationProblem
from .watchlist.api import COOKIE as COOKIE, SESSION_DAYS as SESSION_DAYS, token_hash as token_hash
from .watchlist.api import guest_dependencies, install_watchlist


def utcnow():
    return datetime.now(timezone.utc)


def create_app(settings: Settings | None = None, *, registration_mailer=None):
    config = settings or Settings.from_env()
    from .sources.registry import runtime_registry,identity_key
    source_registry=runtime_registry()
    source_identity_key=identity_key()
    engine = make_engine(config.database_url)

    @asynccontextmanager
    async def lifespan(_):
        ensure_restore_complete(engine)
        if config.auto_create_schema:
            upgrade_schema(engine)
            cleanup_expired_sessions(engine)
            cleanup_expired_accounts(engine)
        seed_catalog(engine)
        async def cleanup_loop():
            while True:
                await asyncio.sleep(3600)
                try:
                    await asyncio.to_thread(cleanup_expired_sessions, engine)
                    await asyncio.to_thread(cleanup_expired_accounts, engine)
                except Exception:
                    logging.getLogger(__name__).error('Expired-session cleanup failed; retry in one hour')

        cleanup = asyncio.create_task(cleanup_loop())
        try:
            yield
        finally:
            cleanup.cancel()
            with suppress(asyncio.CancelledError):
                await cleanup
            engine.dispose()

    app = FastAPI(title='Абитуриент API', version='0.2.0', lifespan=lifespan, docs_url=None if config.environment=='production' else '/api/docs', openapi_url=None if config.environment=='production' else '/api/openapi.json', redoc_url=None, responses={422: {'model': ValidationProblem}})
    app.state.engine = engine
    app.state.source_registry = source_registry

    @app.exception_handler(SQLAlchemyTimeoutError)
    async def database_busy(request, error):
        # Connection pool exhaustion is overload, not a defect: ask the client to retry.
        return JSONResponse({'detail':'Сервис сейчас перегружен. Повторите запрос позже.'},status_code=503,headers={'Retry-After':'5'})

    @app.exception_handler(RequestValidationError)
    async def validation_error(_, error):
        safe_names = {'body','path','query','header','cookie','bundle','watches','history','latest','values','rank','seats','excluded','noConsent','no_consent','university','title','sourceUrl','source_url','createdAt','created_at','capturedAt','captured_at','exportedAt','exported_at','formatVersion','format_version','calculation','modelVersion','model_version','sourceKind','source_kind','id','before','limit','q','watch_id','mode'}
        errors = error.errors()
        locations = [[part if type(part) is int and 0 <= part <= 10000 else part if isinstance(part,str) and part in safe_names else 'field' for part in item.get('loc',())[:12]] for item in errors[:20]]
        problem = ValidationProblem(detail='Проверьте формат и значения запроса.',fields=locations,truncated=len(errors)>20)
        return JSONResponse(problem.model_dump(by_alias=True),status_code=422)
    app.add_middleware(RequestBudgetMiddleware)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(config.allowed_hosts), www_redirect=False)

    @app.middleware('http')
    async def protect_writes(request: Request, call_next):
        # Same-origin fetch with a custom header; no cross-origin CORS is enabled.
        if request.method not in ('GET', 'HEAD', 'OPTIONS'):
            if request.headers.get('X-Requested-With') != 'abiturient' or not permitted_origin(request, config):
                from fastapi.responses import JSONResponse
                return JSONResponse({'detail': 'Запрос должен исходить из интерфейса приложения.'}, status_code=403)
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response

    app.add_middleware(RequestDiagnosticsMiddleware)

    def database():
        with Session(engine) as session:
            yield session

    from .auth.account_api import install as install_accounts
    install_accounts(app, database, config, engine, mailer=registration_mailer)

    def clock():
        return utcnow()

    owner, write_owner = guest_dependencies(engine, database, clock)

    from app.watchlist.source_api import install_source_routes
    install_source_routes(app,database,owner,write_owner,source_registry,source_identity_key,clock)
    from app.competitions.scenario_api import install as install_scenarios
    install_scenarios(app,database,owner,source_registry)
    from app.competitions.competition_api import install as install_competitions
    install_competitions(app,database,owner,registry=source_registry)
    from app.watchlist.changes import install as install_changes
    install_changes(app,database,owner,write_owner,clock)

    install_status_routes(app, database)
    install_legacy_catalog(app, database, source_registry)

    install_watchlist(app, database, owner, write_owner, config.secure_cookie, clock, lambda: uuid4())

    from app.catalog.product_catalog import install as install_product_catalog
    install_product_catalog(app, database)
    return app


app = create_app()
