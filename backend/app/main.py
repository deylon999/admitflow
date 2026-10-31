import asyncio
import hashlib
import logging
import secrets
from contextlib import asynccontextmanager
from contextlib import suppress
from datetime import datetime, timedelta, timezone

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from sqlalchemy import delete, func, select, text
from sqlalchemy.orm import Session

from .calculation import CalculationInput, CalculationResult, calculate
from .config import Settings
from .database import Base, BrowserSession, Snapshot, Watch, make_engine
from .schemas import SessionRead, SnapshotRead, WatchCreate, WatchDetail, WatchRead
from .maintenance import cleanup_expired_sessions

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
            Base.metadata.create_all(engine)
            cleanup_expired_sessions(engine)
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
        if request.method not in ('GET', 'HEAD', 'OPTIONS') and request.url.path != '/api/v1/calculate':
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

    def owner(request: Request, db: Session = Depends(database)):
        token = request.cookies.get(COOKIE, '')
        found = db.scalar(select(BrowserSession).where(BrowserSession.token_hash == token_hash(token), BrowserSession.expires_at > utcnow())) if token else None
        if token and not found:
            raise HTTPException(401, 'Срок гостевой сессии истёк. Начните новую сессию явно.')
        if not found:
            raise HTTPException(401, 'Сессия истекла. Обновите страницу.')
        return found.token_hash

    def watch_owned(watch_id, owner_hash, db):
        watch = db.scalar(select(Watch).where(Watch.id == watch_id, Watch.owner_hash == owner_hash))
        if not watch:
            raise HTTPException(404, 'Направление не найдено.')
        return watch

    def snapshot_read(snapshot):
        values = CalculationInput(rank=snapshot.rank, seats=snapshot.seats, excluded=snapshot.excluded, no_consent=snapshot.no_consent)
        return SnapshotRead(id=snapshot.id, captured_at=utc(snapshot.captured_at), source_kind=snapshot.source_kind, model_version=snapshot.model_version, values=values, calculation=calculate(values))

    def watch_read(watch, db):
        latest = db.scalar(select(Snapshot).where(Snapshot.watch_id == watch.id).order_by(Snapshot.captured_at.desc(), Snapshot.id.desc()).limit(1))
        return WatchRead(id=watch.id, university=watch.university, title=watch.title, source_url=watch.source_url, created_at=utc(watch.created_at), latest=snapshot_read(latest))

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
        return SessionRead(expires_at=utc(db.get(BrowserSession, owner_hash).expires_at))

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
    def create_watch(body: WatchCreate, owner_hash: str = Depends(owner), db: Session = Depends(database)):
        count = db.scalar(select(func.count()).select_from(Watch).where(Watch.owner_hash == owner_hash))
        if count >= 20:
            raise HTTPException(409, 'Можно сохранить до 20 направлений.')
        watch = Watch(owner_hash=owner_hash, university=body.university, title=body.title, source_url=str(body.source_url), created_at=utcnow())
        db.add(watch)
        db.flush()
        add_snapshot(watch.id, body.values, db)
        db.commit()
        return watch_read(watch, db)

    @app.get('/api/v1/watches/{watch_id}', response_model=WatchDetail)
    def get_watch(watch_id: str, owner_hash: str = Depends(owner), db: Session = Depends(database)):
        watch = watch_owned(watch_id, owner_hash, db)
        history = db.scalars(select(Snapshot).where(Snapshot.watch_id == watch_id).order_by(Snapshot.captured_at.desc(), Snapshot.id.desc()).limit(100)).all()
        return WatchDetail(**watch_read(watch, db).model_dump(), history=[snapshot_read(item) for item in history])

    @app.post('/api/v1/watches/{watch_id}/snapshots', response_model=SnapshotRead, status_code=201)
    def update_snapshot(watch_id: str, body: CalculationInput, owner_hash: str = Depends(owner), db: Session = Depends(database)):
        watch_owned(watch_id, owner_hash, db)
        count = db.scalar(select(func.count()).select_from(Snapshot).where(Snapshot.watch_id == watch_id))
        if count >= 500:
            raise HTTPException(409, 'Для направления сохранено максимальное число обновлений: 500.')
        result = add_snapshot(watch_id, body, db)
        db.commit()
        return snapshot_read(result)

    @app.delete('/api/v1/watches/{watch_id}', status_code=204)
    def delete_watch(watch_id: str, owner_hash: str = Depends(owner), db: Session = Depends(database)):
        watch = watch_owned(watch_id, owner_hash, db)
        db.delete(watch)
        db.commit()

    return app


app = create_app()
