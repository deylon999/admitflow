import asyncio
import hashlib
import logging
import secrets
from contextlib import asynccontextmanager
from contextlib import suppress
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import and_, delete, func, or_, select, text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .calculation import AssessmentInput, CalculationInput, CalculationResult, ScenarioAssessment, assess_scenario, calculate, calculate_versioned
from .config import Settings
from .database import BrowserSession, Snapshot, Watch, make_engine
from .schemas import SessionRead, SnapshotRead, WatchCreate, WatchDetail, WatchRead
from .maintenance import cleanup_expired_sessions
from .catalog import search_universities, seed_catalog
from .schemas import CatalogRead, CoverageRead, DataExport, HistoryPage, ImportRequest, ImportResult, SourceStatus, ValidationProblem
from .coverage import coverage
from .importing import import_bundle
from .sources.status import source_status
from .operations import begin_operation, remember_operation, retire_operations
from .migrations import ensure_restore_complete, schema_heads, upgrade_schema
from .http import RequestBudgetMiddleware, RequestDiagnosticsMiddleware, permitted_origin

COOKIE = 'abiturient_session'
SESSION_DAYS = 30


def utcnow():
    return datetime.now(timezone.utc)


def utc(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def create_app(settings: Settings | None = None):
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
        seed_catalog(engine)
        async def cleanup_loop():
            while True:
                await asyncio.sleep(3600)
                try:
                    await asyncio.to_thread(cleanup_expired_sessions, engine)
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

    app = FastAPI(title='Абитуриент API', version='0.2.0', lifespan=lifespan, docs_url='/api/docs', openapi_url='/api/openapi.json', redoc_url=None, responses={422: {'model': ValidationProblem}})
    app.state.engine = engine
    app.state.source_registry = source_registry

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
        if request.method not in ('GET', 'HEAD', 'OPTIONS') and request.url.path not in ('/api/v1/calculate', '/api/v1/assess'):
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

    def identify_owner(request, db, *, lock=False):
        token = request.cookies.get(COOKIE, '')
        if lock and token and engine.dialect.name == 'sqlite':
            db.execute(text('BEGIN IMMEDIATE'))
        query = select(BrowserSession).where(BrowserSession.token_hash == token_hash(token), BrowserSession.expires_at > utcnow())
        if lock:
            query = query.with_for_update()
        found = db.scalar(query) if token else None
        if not found:
            raise HTTPException(401, 'Срок гостевой сессии истёк. Начните новую сессию явно.')
        return found.token_hash

    def owner(request: Request, db: Session = Depends(database)):
        return identify_owner(request, db)

    def write_owner(request: Request, db: Session = Depends(database)):
        return identify_owner(request, db, lock=True)

    def watch_owned(watch_id, owner_hash, db):
        watch = db.scalar(select(Watch).where(Watch.id == watch_id, Watch.owner_hash == owner_hash))
        if not watch:
            raise HTTPException(404, 'Направление не найдено.')
        return watch

    from .source_api import install_source_routes
    install_source_routes(app,database,owner,write_owner,source_registry,source_identity_key,lambda:utcnow())

    def snapshot_read(snapshot):
        values = CalculationInput(rank=snapshot.rank, seats=snapshot.seats, excluded=snapshot.excluded, no_consent=snapshot.no_consent)
        try:result=calculate_versioned(values,snapshot.model_version)
        except ValueError:raise HTTPException(409,'Версия сохранённого ручного расчёта не поддержана. Старые данные не пересчитаны новой моделью.') from None
        return SnapshotRead(id=snapshot.id, captured_at=utc(snapshot.captured_at), source_kind=snapshot.source_kind, model_version=snapshot.model_version, values=values, calculation=result)

    def watch_read(watch, db, latest=None):
        latest = latest or db.scalar(select(Snapshot).where(Snapshot.watch_id == watch.id).order_by(Snapshot.captured_at.desc(), Snapshot.id.desc()).limit(1))
        return WatchRead(id=watch.id, university=watch.university, title=watch.title, source_url=watch.source_url, created_at=utc(watch.created_at), latest=snapshot_read(latest))

    def watch_detail(watch, db, limit=100):
        history = db.scalars(select(Snapshot).where(Snapshot.watch_id == watch.id).order_by(Snapshot.captured_at.desc(), Snapshot.id.desc()).limit(limit)).all()
        if not history or len(history) > 500:
            raise HTTPException(409, 'История направления не соответствует ограничениям сервиса.')
        return WatchDetail(**watch_read(watch, db, latest=history[0]).model_dump(), history=[snapshot_read(item) for item in history])

    def batch_watches(watches, db, *, full=False):
        if not watches:
            return []
        ids = [watch.id for watch in watches]
        if full:
            rows = db.scalars(select(Snapshot).where(Snapshot.watch_id.in_(ids)).order_by(Snapshot.watch_id, Snapshot.captured_at.desc(), Snapshot.id.desc()).limit(10001)).all()
        else:
            ranked = select(Snapshot.id, func.row_number().over(partition_by=Snapshot.watch_id, order_by=(Snapshot.captured_at.desc(), Snapshot.id.desc())).label('position')).where(Snapshot.watch_id.in_(ids)).subquery()
            rows = db.scalars(select(Snapshot).join(ranked, Snapshot.id == ranked.c.id).where(ranked.c.position == 1)).all()
        grouped = {id: [] for id in ids}
        for row in rows:
            grouped[row.watch_id].append(row)
        result = []
        for watch in watches:
            history = grouped[watch.id]
            if not 1 <= len(history) <= 500:
                raise HTTPException(409,'История направления не соответствует ограничениям сервиса.')
            value = watch_read(watch, db, latest=history[0])
            result.append(WatchDetail(**value.model_dump(),history=[snapshot_read(row) for row in history]) if full else value)
        return result

    def add_snapshot(watch_id, values, db):
        captured = utcnow()
        watch = db.get(Watch, watch_id)
        previous = db.scalar(select(Snapshot).where(Snapshot.watch_id == watch_id).order_by(Snapshot.captured_at.desc(), Snapshot.id.desc()).limit(1))
        if captured < utc(watch.created_at) or (previous and captured < utc(previous.captured_at)):
            raise HTTPException(409,'Время предыдущего сохранения опережает серверное. Проверьте часы или повторите позже.')
        identifier = str(uuid4())
        if previous and captured == utc(previous.captured_at) and identifier <= previous.id:
            try:
                identifier = str(UUID(int=UUID(previous.id).int + 1))
            except (ValueError, OverflowError):
                raise HTTPException(409,'Не удалось упорядочить сохранение. Повторите позже.') from None
        snapshot = Snapshot(id=identifier,watch_id=watch_id, captured_at=captured, **values.model_dump())
        db.add(snapshot)
        db.flush()
        return snapshot

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

    @app.post('/api/v1/calculate', response_model=CalculationResult)
    def calculate_endpoint(values: CalculationInput):
        return calculate(values)

    @app.post('/api/v1/assess', response_model=ScenarioAssessment)
    def assess_endpoint(body: AssessmentInput):
        return assess_scenario(body)

    @app.get('/api/v1/universities', response_model=CatalogRead)
    def universities(q: str = Query('', max_length=120), db: Session = Depends(database)):
        return search_universities(db, q)

    from .source_catalog import GroupCatalog,groups as search_groups
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

    @app.get('/api/v1/export', response_model=DataExport)
    def export_data(response: Response, owner_hash: str = Depends(write_owner), db: Session = Depends(database)):
        # Hold the owner's lock for a consistent read; no data is changed.
        watches = db.scalars(select(Watch).where(Watch.owner_hash == owner_hash).order_by(Watch.created_at.desc(), Watch.id.desc()).limit(21)).all()
        if len(watches) > 20:
            raise HTTPException(409, 'Количество направлений превышает лимит экспорта.')
        result = batch_watches(watches, db, full=True)
        exported = utcnow()
        if any(watch.created_at > exported or any(snapshot.captured_at > exported for snapshot in watch.history) for watch in result):
            raise HTTPException(409, 'Время сохранённых данных опережает серверное. Проверьте часы или повторите экспорт позже.')
        response.headers['Content-Disposition'] = 'attachment; filename="admitflow-export.json"'
        return DataExport(exported_at=exported, watches=result)

    @app.post('/api/v1/session', status_code=204)
    def start_session(request: Request, response: Response, db: Session = Depends(database)):
        token = request.cookies.get(COOKIE, '')
        found = db.scalar(select(BrowserSession).where(BrowserSession.token_hash == token_hash(token), BrowserSession.expires_at > utcnow())) if token else None
        if token and not found:
            raise HTTPException(401, 'Срок гостевой сессии истёк. Начните новую сессию явно.')
        if not found:
            token = secrets.token_urlsafe(32)
            db.add(BrowserSession(token_hash=token_hash(token), expires_at=utcnow() + timedelta(days=SESSION_DAYS)))
            db.commit()
            response.set_cookie(COOKIE, token, httponly=True, secure=config.secure_cookie, samesite='lax', max_age=SESSION_DAYS * 86400, path='/api')

    @app.post('/api/v1/import', response_model=ImportResult, status_code=201)
    def import_data(body: ImportRequest, request: Request, owner_hash: str = Depends(write_owner), db: Session = Depends(database)):
        if not request.headers.get('Idempotency-Key'):
            raise HTTPException(400,'Для импорта нужен ключ операции.')
        key,fingerprint,cached=begin_operation(request,body,owner_hash,db)
        if cached is not None:
            return {**cached,'replayed':True}
        count,snapshots=import_bundle(db,owner_hash,body.bundle,utcnow())
        result=ImportResult(imported_count=count,snapshot_count=snapshots)
        # Only aggregate counts are cached; deleting a watch leaves no import payload.
        remember_operation(db,owner_hash,key,fingerprint,None,result)
        db.commit()
        return result

    @app.get('/api/v1/session', response_model=SessionRead)
    def get_session(owner_hash: str = Depends(owner), db: Session = Depends(database)):
        session = db.get(BrowserSession, owner_hash)
        if session is None:
            raise HTTPException(401, 'Сессия завершена.')
        scope = hashlib.sha256(f'admitflow-draft-v1:{owner_hash}'.encode()).hexdigest()
        return SessionRead(expires_at=utc(session.expires_at), draft_scope=scope)

    @app.delete('/api/v1/session', status_code=204)
    def delete_session(request: Request, response: Response, db: Session = Depends(database)):
        # Explicit reset also works with an expired/unknown token and is idempotent.
        token = request.cookies.get(COOKIE)
        if token:
            db.execute(delete(BrowserSession).where(BrowserSession.token_hash == token_hash(token)))
            db.commit()
        response.delete_cookie(COOKIE, path='/api', secure=config.secure_cookie, httponly=True, samesite='lax')

    @app.get('/api/v1/watches', response_model=list[WatchRead])
    def list_watches(owner_hash: str = Depends(owner), db: Session = Depends(database)):
        watches = db.scalars(select(Watch).where(Watch.owner_hash == owner_hash).order_by(Watch.created_at.desc()).limit(20)).all()
        return batch_watches(watches, db)

    @app.post('/api/v1/watches', response_model=WatchRead, status_code=201)
    def create_watch(body: WatchCreate, request: Request, owner_hash: str = Depends(write_owner), db: Session = Depends(database)):
        key, fingerprint, cached = begin_operation(request, body, owner_hash, db)
        if cached is not None:
            return cached
        from .direction_budget import direction_budget
        count = direction_budget(db,owner_hash).total
        if count >= 20:
            raise HTTPException(409, 'Можно сохранить до 20 направлений.')
        watch = Watch(owner_hash=owner_hash, university=body.university, title=body.title, source_url=str(body.source_url), created_at=utcnow())
        db.add(watch)
        db.flush()
        add_snapshot(watch.id, body.values, db)
        result = watch_read(watch, db)
        remember_operation(db, owner_hash, key, fingerprint, watch.id, result)
        db.commit()
        return result

    @app.get('/api/v1/watches/{watch_id}', response_model=WatchDetail)
    def get_watch(watch_id: str, owner_hash: str = Depends(owner), db: Session = Depends(database)):
        watch = watch_owned(watch_id, owner_hash, db)
        return watch_detail(watch, db)

    @app.post('/api/v1/watches/{watch_id}/snapshots', response_model=SnapshotRead, status_code=201)
    def update_snapshot(watch_id: str, body: CalculationInput, request: Request, owner_hash: str = Depends(write_owner), db: Session = Depends(database)):
        key, fingerprint, cached = begin_operation(request, body, owner_hash, db)
        if cached is not None:
            return cached
        watch_owned(watch_id, owner_hash, db)
        expected = request.headers.getlist('X-Expected-Snapshot')
        if expected:
            if len(expected) != 1 or not expected[0] or len(expected[0]) > 100 or expected[0].strip() != expected[0] or any(ord(char) < 32 or ord(char) == 127 for char in expected[0]):
                raise HTTPException(400, 'Некорректная версия исходного сохранения.')
            latest = db.scalar(select(Snapshot.id).where(Snapshot.watch_id == watch_id).order_by(Snapshot.captured_at.desc(), Snapshot.id.desc()).limit(1))
            if latest != expected[0]:
                raise HTTPException(409, 'У направления есть более новое сохранение. Обновите кабинет и проверьте цифры перед новой отправкой.')
        count = db.scalar(select(func.count()).select_from(Snapshot).where(Snapshot.watch_id == watch_id))
        if count >= 500:
            raise HTTPException(409, 'Для направления сохранено максимальное число обновлений: 500.')
        result = snapshot_read(add_snapshot(watch_id, body, db))
        remember_operation(db, owner_hash, key, fingerprint, watch_id, result)
        db.commit()
        return result

    @app.delete('/api/v1/watches/{watch_id}', status_code=204)
    def delete_watch(watch_id: str, owner_hash: str = Depends(write_owner), db: Session = Depends(database)):
        watch = watch_owned(watch_id, owner_hash, db)
        retire_operations(db, watch_id)
        db.delete(watch)
        db.commit()

    @app.get('/api/v1/watches/{watch_id}/history', response_model=HistoryPage)
    def history_page(watch_id: str, before: str | None = Query(None, max_length=100), limit: int = Query(100, ge=1, le=100), owner_hash: str = Depends(owner), db: Session = Depends(database)):
        watch_owned(watch_id, owner_hash, db)
        query = select(Snapshot).where(Snapshot.watch_id == watch_id)
        if before is not None:
            cursor = db.scalar(select(Snapshot).where(Snapshot.id == before, Snapshot.watch_id == watch_id))
            if cursor is None:
                raise HTTPException(400, 'Курсор истории недействителен. Загрузите историю заново.')
            query = query.where(or_(Snapshot.captured_at < cursor.captured_at, and_(Snapshot.captured_at == cursor.captured_at, Snapshot.id < cursor.id)))
        rows = db.scalars(query.order_by(Snapshot.captured_at.desc(), Snapshot.id.desc()).limit(limit + 1)).all()
        total = db.scalar(select(func.count()).select_from(Snapshot).where(Snapshot.watch_id == watch_id))
        return HistoryPage(items=[snapshot_read(row) for row in rows[:limit]], next_cursor=rows[limit - 1].id if len(rows) > limit else None, total=total)

    return app


app = create_app()
