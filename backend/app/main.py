import asyncio
import hashlib
import logging
import secrets
from contextlib import asynccontextmanager
from contextlib import suppress
from datetime import datetime, timedelta, timezone

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from sqlalchemy import and_, delete, func, or_, select, text
from sqlalchemy.orm import Session

from .calculation import AssessmentInput, CalculationInput, CalculationResult, ScenarioAssessment, assess_scenario, calculate
from .config import Settings
from .database import BrowserSession, Snapshot, Watch, make_engine
from .schemas import SessionRead, SnapshotRead, WatchCreate, WatchDetail, WatchRead
from .maintenance import cleanup_expired_sessions
from .catalog import search_universities, seed_catalog
from .schemas import CatalogRead, DataExport, HistoryPage, SourceStatus
from .sources.status import source_status
from .operations import begin_operation, remember_operation, retire_operations
from .migrations import upgrade_schema

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
    engine = make_engine(config.database_url)

    @asynccontextmanager
    async def lifespan(_):
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

    app = FastAPI(title='Абитуриент API', version='0.2.0', lifespan=lifespan, docs_url='/api/docs', openapi_url='/api/openapi.json', redoc_url=None)
    app.state.engine = engine

    @app.middleware('http')
    async def protect_writes(request: Request, call_next):
        # Same-origin fetch with a custom header; no cross-origin CORS is enabled.
        if request.method not in ('GET', 'HEAD', 'OPTIONS') and request.url.path not in ('/api/v1/calculate', '/api/v1/assess'):
            if request.headers.get('X-Requested-With') != 'abiturient':
                from fastapi.responses import JSONResponse
                return JSONResponse({'detail': 'Запрос должен исходить из интерфейса приложения.'}, status_code=403)
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response

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

    def snapshot_read(snapshot):
        values = CalculationInput(rank=snapshot.rank, seats=snapshot.seats, excluded=snapshot.excluded, no_consent=snapshot.no_consent)
        return SnapshotRead(id=snapshot.id, captured_at=utc(snapshot.captured_at), source_kind=snapshot.source_kind, model_version=snapshot.model_version, values=values, calculation=calculate(values))

    def watch_read(watch, db, latest=None):
        latest = latest or db.scalar(select(Snapshot).where(Snapshot.watch_id == watch.id).order_by(Snapshot.captured_at.desc(), Snapshot.id.desc()).limit(1))
        return WatchRead(id=watch.id, university=watch.university, title=watch.title, source_url=watch.source_url, created_at=utc(watch.created_at), latest=snapshot_read(latest))

    def watch_detail(watch, db, limit=100):
        history = db.scalars(select(Snapshot).where(Snapshot.watch_id == watch.id).order_by(Snapshot.captured_at.desc(), Snapshot.id.desc()).limit(limit)).all()
        if not history or len(history) > 500:
            raise HTTPException(409, 'История направления не соответствует ограничениям сервиса.')
        return WatchDetail(**watch_read(watch, db, latest=history[0]).model_dump(), history=[snapshot_read(item) for item in history])

    def add_snapshot(watch_id, values, db):
        snapshot = Snapshot(watch_id=watch_id, captured_at=utcnow(), **values.model_dump())
        db.add(snapshot)
        db.flush()
        return snapshot

    @app.get('/api/health')
    def health(db: Session = Depends(database)):
        db.execute(text('SELECT 1'))
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

    @app.get('/api/v1/sources/{source_id}/status', response_model=SourceStatus)
    def get_source_status(source_id: str, db: Session = Depends(database)):
        result = source_status(db,source_id)
        if result is None:
            raise HTTPException(404,'Источник не найден.')
        return result

    @app.get('/api/v1/export', response_model=DataExport)
    def export_data(response: Response, owner_hash: str = Depends(write_owner), db: Session = Depends(database)):
        # Hold the owner's lock for a consistent read; no data is changed.
        watches = db.scalars(select(Watch).where(Watch.owner_hash == owner_hash).order_by(Watch.created_at.desc(), Watch.id.desc()).limit(21)).all()
        if len(watches) > 20:
            raise HTTPException(409, 'Количество направлений превышает лимит экспорта.')
        response.headers['Content-Disposition'] = 'attachment; filename="admitflow-export.json"'
        return DataExport(exported_at=utcnow(), watches=[watch_detail(watch, db, limit=501) for watch in watches])

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

    @app.get('/api/v1/session', response_model=SessionRead)
    def get_session(owner_hash: str = Depends(owner), db: Session = Depends(database)):
        session = db.get(BrowserSession, owner_hash)
        if session is None:
            raise HTTPException(401, 'Сессия завершена.')
        return SessionRead(expires_at=utc(session.expires_at))

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
        return [watch_read(watch, db) for watch in watches]

    @app.post('/api/v1/watches', response_model=WatchRead, status_code=201)
    def create_watch(body: WatchCreate, request: Request, owner_hash: str = Depends(write_owner), db: Session = Depends(database)):
        key, fingerprint, cached = begin_operation(request, body, owner_hash, db)
        if cached is not None:
            return cached
        count = db.scalar(select(func.count()).select_from(Watch).where(Watch.owner_hash == owner_hash))
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
        return HistoryPage(items=[snapshot_read(row) for row in rows[:limit]], next_cursor=rows[limit - 1].id if len(rows) > limit else None)

    return app


app = create_app()
