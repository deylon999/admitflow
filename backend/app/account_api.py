"""Account-only API. Guest owner/session lifecycle is deliberately independent."""
from datetime import datetime, timedelta, timezone
import logging
import secrets
from uuid import uuid4

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .account_dto import AccountRead, AccountSessionRead, CsrfRead, EmptyAuthRequest, LoginRequest, RegistrationRead, RegistrationRequest
from .account_limits import AuthRateExceeded, Budget, consume_budgets
from .account_mail import UnavailableRegistrationMailer
from .account_security import InvalidAccountInput, PasswordCapacityError, credential_digest, hash_password, new_token, verify_password
from .accounts import AccountActionToken, AccountCsrfContext, AccountRefreshToken, AccountSession, AccountUser
from .http import permitted_origin

ACCESS_COOKIE = 'admitflow_access'
CSRF_COOKIE = 'admitflow_csrf_context'
REFRESH_COOKIE = 'admitflow_refresh'
ACCESS_PATH = '/api/v1'
REFRESH_PATH = '/api/v1/auth'
ACCESS_SECONDS = 900
IDLE_SECONDS = 7*86400
ANONYMOUS_CSRF_SECONDS = 1800


class AuthProblem(Exception):
    def __init__(self, status, code, detail):
        self.status, self.code, self.detail = status, code, detail


def unavailable():
    return AuthProblem(503, 'auth_unavailable', 'Авторизация временно недоступна.')


def unauthenticated():
    return AuthProblem(401, 'not_authenticated', 'Не удалось подтвердить доступ к аккаунту.')


def csrf_invalid():
    return AuthProblem(403, 'csrf_invalid', 'Обновите страницу и повторите действие.')


class AuthRoute(APIRoute):
    def get_route_handler(self):
        original = super().get_route_handler()
        async def handle(request):
            try:
                return await original(request)
            except AuthProblem as exc:
                return JSONResponse({'code': exc.code, 'detail': exc.detail}, status_code=exc.status)
            except AuthRateExceeded as exc:
                return JSONResponse({'code': 'rate_limited', 'detail': 'Слишком много запросов. Повторите позже.'},
                                    status_code=429, headers={'Retry-After': str(exc.retry_after)})
            except InvalidAccountInput:
                return JSONResponse({'code': 'invalid_input', 'detail': 'Проверьте формат и значения запроса.'}, status_code=422)
            except (PasswordCapacityError, SQLAlchemyError):
                return JSONResponse({'code': 'auth_unavailable', 'detail': 'Авторизация временно недоступна.'},
                                    status_code=503, headers={'Retry-After': '5'})
        return handle


def utc(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def digest_or_none(purpose, token):
    try:
        return credential_digest(purpose, token)
    except InvalidAccountInput:
        return None


def current_account(db, request, now):
    digest = digest_or_none('access', request.cookies.get(ACCESS_COOKIE))
    # Join the user for every read: disabling or password-reset revocation is immediate.
    row = db.execute(select(AccountSession, AccountUser).join(AccountUser, AccountSession.user_id == AccountUser.id)
                     .where(AccountSession.access_hash == digest)
                     .execution_options(populate_existing=True)).first() if digest else None
    if row and active_family(*row, now):
        if utc(row[0].access_expires_at) > now:
            return row
        token = db.scalar(select(AccountRefreshToken).where(AccountRefreshToken.session_id == row[0].id,
                          AccountRefreshToken.consumed_at.is_(None), AccountRefreshToken.expires_at > now))
        supplied_refresh = request.cookies.get(REFRESH_COOKIE)
        if token and (not supplied_refresh or digest_or_none('refresh', supplied_refresh) == token.token_hash):
            raise access_expired()
    if not request.cookies.get(ACCESS_COOKIE) and fresh_refresh_account(db, request, now):
        raise access_expired()
    raise unauthenticated()


def access_expired():
    return AuthProblem(401, 'access_expired', 'Срок доступа истёк. Обновите сессию.')


def active_family(session, user, now):
    return (session.revoked_at is None and utc(session.expires_at) > now
            and utc(session.idle_expires_at) > now and user.status == 'active'
            and user.email_verified_at is not None)


def fresh_refresh_account(db, request, now):
    digest = digest_or_none('refresh', request.cookies.get(REFRESH_COOKIE))
    row = db.execute(select(AccountSession, AccountUser, AccountRefreshToken)
                     .join(AccountUser, AccountSession.user_id == AccountUser.id)
                     .join(AccountRefreshToken, AccountRefreshToken.session_id == AccountSession.id)
                     .where(AccountRefreshToken.token_hash == digest)
                     .execution_options(populate_existing=True)).first() if digest else None
    if (row and active_family(row[0], row[1], now) and row[2].consumed_at is None
            and utc(row[2].expires_at) > now):
        return row
    return None


def read_csrf_context(db, request, now, *, lock=False):
    digest = digest_or_none('csrf_context', request.cookies.get(CSRF_COOKIE))
    query = select(AccountCsrfContext).where(AccountCsrfContext.token_hash == digest,
                                            AccountCsrfContext.expires_at > now)
    if lock:
        query = query.with_for_update().execution_options(populate_existing=True)
    context = db.scalar(query) if digest else None
    supplied = request.headers.get('X-CSRF-Token', '')
    if not context or len(supplied) > 64 or not secrets.compare_digest(context.csrf_token.encode(), supplied.encode()):
        raise csrf_invalid()
    return context


def csrf_context(db, request, now, *, lock=False):
    context = read_csrf_context(db, request, now, lock=lock)
    if context.session_id is not None:
        try:
            session, _ = current_account(db, request, now)
        except AuthProblem:
            refreshed = fresh_refresh_account(db, request, now)
            if not refreshed:
                raise csrf_invalid() from None
            session = refreshed[0]
        if context.session_id != session.id:
            raise csrf_invalid()
    return context


def discover_family(db, request, *, refresh_only=False):
    """Discover IDs without taking locks or caching mutable ORM objects."""
    digest = digest_or_none('refresh', request.cookies.get(REFRESH_COOKIE))
    found = db.execute(select(AccountSession.user_id, AccountSession.id)
                       .join(AccountRefreshToken, AccountRefreshToken.session_id == AccountSession.id)
                       .where(AccountRefreshToken.token_hash == digest)).first() if digest else None
    if not found and not refresh_only:
        access = digest_or_none('access', request.cookies.get(ACCESS_COOKIE))
        found = db.execute(select(AccountSession.user_id, AccountSession.id)
                           .where(AccountSession.access_hash == access)).first() if access else None
    return found


def lock_family(db, ids):
    # Use the same lock order for refresh, logout and future password reset.
    user = db.scalar(select(AccountUser).where(AccountUser.id == ids[0]).with_for_update()
                     .execution_options(populate_existing=True))
    session = db.scalar(select(AccountSession).where(AccountSession.id == ids[1],
                        AccountSession.user_id == ids[0]).with_for_update()
                        .execution_options(populate_existing=True)) if user else None
    if not session:
        raise unauthenticated()
    return session, user


def reject_mixed_access(db, request, session_id):
    digest = digest_or_none('access', request.cookies.get(ACCESS_COOKIE))
    other = db.scalar(select(AccountSession.id).where(AccountSession.access_hash == digest)) if digest else None
    if other is not None and other != session_id:
        raise csrf_invalid()


def revoke_family(db, session, now):
    if session.revoked_at is None:
        session.revoked_at = now
    db.execute(update(AccountRefreshToken).where(AccountRefreshToken.session_id == session.id,
               AccountRefreshToken.consumed_at.is_(None)).values(consumed_at=now)
               .execution_options(synchronize_session=False))
    # A short CSRF tombstone permits authenticated duplicate logout, never access.
    deadline = now+timedelta(seconds=ANONYMOUS_CSRF_SECONDS)
    db.execute(update(AccountCsrfContext).where(AccountCsrfContext.session_id == session.id,
               AccountCsrfContext.expires_at > deadline).values(expires_at=deadline)
               .execution_options(synchronize_session=False))


def set_credentials(response, access, refresh, session, config, now):
    for name, value, path, deadline in (
        (ACCESS_COOKIE, access, ACCESS_PATH, session.access_expires_at),
        (REFRESH_COOKIE, refresh, REFRESH_PATH, session.idle_expires_at),
    ):
        response.set_cookie(name, value, path=path, max_age=max(1, int((utc(deadline)-now).total_seconds())),
                            httponly=True, secure=config.secure_cookie, samesite='lax')


def set_context_cookie(response, token, config, seconds):
    response.set_cookie(CSRF_COOKIE, token, path=ACCESS_PATH, max_age=seconds,
                        httponly=True, secure=config.secure_cookie, samesite='lax')


def make_context(db, now, *, session_id=None, seconds=ANONYMOUS_CSRF_SECONDS):
    token = new_token()
    context = AccountCsrfContext(token_hash=credential_digest('csrf_context', token), csrf_token=new_token(),
                                 session_id=session_id, created_at=now, expires_at=now+timedelta(seconds=seconds))
    db.add(context)
    return token, context


def session_read(session, user):
    return AccountSessionRead(account=AccountRead(id=user.id, email=user.email),
                              access_expires_at=utc(session.access_expires_at), absolute_expires_at=utc(session.expires_at))


def install(app, database, config, engine, *, mailer=None, clock=None):
    mailer = mailer if mailer is not None else UnavailableRegistrationMailer()
    clock = clock or (lambda: datetime.now(timezone.utc))
    router = APIRouter(prefix='/api/v1/auth', route_class=AuthRoute)

    def enabled():
        if not config.auth_enabled:
            raise unavailable()

    def peer(request):
        # Do not accept arbitrary forwarded headers; current proxy peer is an aggregate.
        return request.client.host if request.client else 'unknown-peer'

    def rate(request, operation, limit, seconds, *, email=None):
        rules = [Budget(operation+'-peer', ('peer', peer(request)), limit, seconds)]
        if email is not None:
            rules.append(Budget(operation+'-pair', ('email-peer', email, peer(request)), 10, 900))
        consume_budgets(engine, config.auth_rate_key, rules, now=clock())

    def guard(operation, limit, seconds):
        def check(request: Request, _=Depends(enabled)):
            rate(request, operation, limit, seconds)
        return check

    @router.get('/csrf', response_model=CsrfRead, dependencies=[Depends(guard('csrf', 120, 900))])
    def csrf(request: Request, response: Response, db: Session = Depends(database)):
        if request.headers.get('X-Requested-With') != 'abiturient' or not permitted_origin(request, config):
            raise csrf_invalid()
        now = clock()
        # A current refresh can restore bound CSRF after the browser drops access.
        # A spent refresh cannot bootstrap a bound context; GET never rotates it.
        try:
            session, _ = current_account(db, request, now)
            session_id = session.id
        except AuthProblem:
            refreshed = fresh_refresh_account(db, request, now)
            session = refreshed[0] if refreshed else None
            session_id = session.id if session else None
        if session_id:
            session, user = lock_family(db, (session.user_id, session_id))
            now = clock()
            access_valid = (session.access_hash == digest_or_none('access', request.cookies.get(ACCESS_COOKIE))
                            and utc(session.access_expires_at) > now)
            refreshed = fresh_refresh_account(db, request, now)
            if not active_family(session, user, now) or not (access_valid or (refreshed and refreshed[0].id == session_id)):
                session_id = None
        digest = digest_or_none('csrf_context', request.cookies.get(CSRF_COOKIE))
        context = db.scalar(select(AccountCsrfContext).where(AccountCsrfContext.token_hash == digest,
                            AccountCsrfContext.expires_at > now)) if digest else None
        if context and context.session_id == session_id:
            return CsrfRead(csrf_token=context.csrf_token)
        seconds = max(1, int((utc(session.idle_expires_at)-now).total_seconds())) if session_id else ANONYMOUS_CSRF_SECONDS
        token, context = make_context(db, now, session_id=session_id, seconds=seconds)
        db.commit()
        set_context_cookie(response, token, config, seconds)
        return CsrfRead(csrf_token=context.csrf_token)

    @router.post('/register', response_model=RegistrationRead, status_code=202,
                 dependencies=[Depends(guard('register', 10, 3600))])
    def register(body: RegistrationRequest, request: Request, db: Session = Depends(database)):
        now = clock()
        csrf_context(db, request, now)
        if not mailer.available:
            raise unavailable()  # Same result before user lookup for every address.
        allowed = consume_budgets(engine, config.auth_rate_key,
                                 [Budget('register-email', ('email', body.email), 3, 3600, soft=True)], now=now)
        encoded = hash_password(body.password.get_secret_value())  # Same expensive path on duplicates.
        if not allowed:
            return RegistrationRead()
        token = new_token()
        insert = pg_insert if engine.dialect.name == 'postgresql' else sqlite_insert
        new_id = str(uuid4())
        created = db.scalar(insert(AccountUser).values(id=new_id, email=body.email, password_hash=encoded,
                           status='active', password_changed_at=now, created_at=now, updated_at=now)
                           .on_conflict_do_nothing(index_elements=[AccountUser.email]).returning(AccountUser.id))
        if created:
            db.add(AccountActionToken(token_hash=credential_digest('verify_email', token), user_id=created,
                                     purpose='verify_email', created_at=now, expires_at=now+timedelta(hours=24)))
        db.commit()
        # Every accepted address invokes delivery, including duplicates. None means
        # an existing-account notice (no new token/password mutation). Identical
        # provider failures cannot distinguish new from existing accounts.
        try:
            mailer.deliver_registration(body.email, token if created else None)
        except Exception:
            raise unavailable() from None
        return RegistrationRead()

    @router.post('/login', response_model=AccountSessionRead,
                 dependencies=[Depends(guard('login', 30, 900))])
    def login(body: LoginRequest, request: Request, response: Response, db: Session = Depends(database)):
        csrf_context(db, request, clock())
        consume_budgets(engine, config.auth_rate_key,
                        [Budget('login-pair', ('email-peer', body.email, peer(request)), 10, 900)], now=clock())
        found = db.execute(select(AccountUser.id, AccountUser.password_hash).where(AccountUser.email == body.email)).first()
        user_id, encoded = found if found else (None, None)
        db.rollback()  # Do not hold a connection/user lock while running Argon2id.
        checked = verify_password(body.password.get_secret_value(), encoded)
        if not checked.valid:
            raise unauthenticated()
        user = db.scalar(select(AccountUser).where(AccountUser.id == user_id).with_for_update())
        if (not user or user.password_hash != encoded or user.status != 'active'
                or user.email_verified_at is None):
            raise unauthenticated()
        now = clock()
        # Lock and consume the browser context after the user lock. A second login
        # from the same preauth context cannot issue another session concurrently.
        context = csrf_context(db, request, now, lock=True)
        if checked.needs_rehash:
            user.password_hash = hash_password(body.password.get_secret_value())
            user.updated_at = now
        access = new_token()
        session = AccountSession(user_id=user.id, access_hash=credential_digest('access', access), created_at=now,
                                 access_expires_at=now+timedelta(seconds=ACCESS_SECONDS),
                                 idle_expires_at=now+timedelta(days=7), expires_at=now+timedelta(days=30))
        db.add(session); db.flush()
        db.delete(context)
        refresh = new_token()
        db.add(AccountRefreshToken(token_hash=credential_digest('refresh', refresh), session_id=session.id,
                                  created_at=now, expires_at=session.idle_expires_at))
        context_token, _ = make_context(db, now, session_id=session.id, seconds=IDLE_SECONDS)
        result = session_read(session, user)
        db.commit()  # Credentials are never emitted before successful persistence.
        set_credentials(response, access, refresh, session, config, now)
        set_context_cookie(response, context_token, config, IDLE_SECONDS)
        return result

    @router.post('/refresh', response_model=AccountSessionRead,
                 dependencies=[Depends(guard('refresh', 120, 900))])
    def refresh(body: EmptyAuthRequest, request: Request, response: Response, db: Session = Depends(database)):
        read_csrf_context(db, request, clock())
        ids = discover_family(db, request, refresh_only=True)
        if not ids:
            raise unauthenticated()
        consume_budgets(engine, config.auth_rate_key,
                        [Budget('refresh-session', ('session', ids[1]), 60, 900)], now=clock())
        session, user = lock_family(db, ids)
        digest = digest_or_none('refresh', request.cookies.get(REFRESH_COOKIE))
        token = db.scalar(select(AccountRefreshToken).where(AccountRefreshToken.token_hash == digest,
                          AccountRefreshToken.session_id == session.id).with_for_update())
        now = clock()
        context = read_csrf_context(db, request, now, lock=True)
        if context.session_id != session.id:
            raise csrf_invalid()
        reject_mixed_access(db, request, session.id)
        if not token or not active_family(session, user, now):
            raise unauthenticated()
        if token.consumed_at is not None:
            revoke_family(db, session, now)
            db.commit()  # Raising first would roll back the security response.
            logging.getLogger('admitflow.auth').warning('Refresh credential reuse revoked an account session.')
            raise unauthenticated()
        if utc(token.expires_at) <= now:
            raise unauthenticated()
        access, refreshed = new_token(), new_token()
        token.consumed_at = now
        session.idle_expires_at = min(now+timedelta(seconds=IDLE_SECONDS), utc(session.expires_at))
        session.access_expires_at = min(now+timedelta(seconds=ACCESS_SECONDS), utc(session.expires_at))
        session.access_hash = credential_digest('access', access)
        db.add(AccountRefreshToken(token_hash=credential_digest('refresh', refreshed), session_id=session.id,
                                  created_at=now, expires_at=session.idle_expires_at))
        context.expires_at = session.idle_expires_at
        result = session_read(session, user)
        db.commit()
        set_credentials(response, access, refreshed, session, config, now)
        set_context_cookie(response, request.cookies[CSRF_COOKIE], config,
                           max(1, int((utc(session.idle_expires_at)-now).total_seconds())))
        return result

    @router.get('/session', response_model=AccountSessionRead,
                dependencies=[Depends(guard('session', 600, 900))])
    def session(request: Request, db: Session = Depends(database)):
        account_session, user = current_account(db, request, clock())
        return session_read(account_session, user)

    @router.post('/logout', status_code=204, response_class=Response,
                 dependencies=[Depends(guard('logout', 60, 900))])
    def logout(body: EmptyAuthRequest, request: Request, response: Response, db: Session = Depends(database)):
        read_csrf_context(db, request, clock())
        ids = discover_family(db, request)
        if ids:
            consume_budgets(engine, config.auth_rate_key,
                            [Budget('logout-session', ('session', ids[1]), 60, 900)], now=clock())
            session, user = lock_family(db, ids)
            digest = digest_or_none('refresh', request.cookies.get(REFRESH_COOKIE))
            if digest:
                db.scalar(select(AccountRefreshToken).where(AccountRefreshToken.token_hash == digest,
                          AccountRefreshToken.session_id == session.id).with_for_update())
            now = clock()
            context = read_csrf_context(db, request, now, lock=True)
            if context.session_id != session.id:
                if context.session_id is not None or active_family(session, user, now):
                    raise csrf_invalid()
            reject_mixed_access(db, request, session.id)
            revoke_family(db, session, now)
            db.commit()
        else:
            context = read_csrf_context(db, request, clock(), lock=True)
            if context.session_id is not None:
                raise csrf_invalid()
            db.rollback()  # Anonymous logout has no account/guest data to mutate.
        # Do not emit deletion cookies until server revocation has committed.
        for name, path in ((ACCESS_COOKIE, ACCESS_PATH), (REFRESH_COOKIE, REFRESH_PATH), (CSRF_COOKIE, ACCESS_PATH)):
            response.delete_cookie(name, path=path, httponly=True, secure=config.secure_cookie, samesite='lax')
        response.status_code = 204
        return response

    app.include_router(router)
