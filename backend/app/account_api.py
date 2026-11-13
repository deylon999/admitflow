"""Account-only API. Guest owner/session lifecycle is deliberately independent."""
from datetime import datetime, timedelta, timezone
import secrets
from uuid import uuid4

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .account_dto import AccountRead, AccountSessionRead, CsrfRead, RegistrationRead, RegistrationRequest
from .account_limits import AuthRateExceeded, Budget, consume_budgets
from .account_mail import UnavailableRegistrationMailer
from .account_security import InvalidAccountInput, PasswordCapacityError, credential_digest, hash_password, new_token
from .accounts import AccountActionToken, AccountCsrfContext, AccountSession, AccountUser
from .http import permitted_origin

ACCESS_COOKIE = 'admitflow_access'
CSRF_COOKIE = 'admitflow_csrf_context'
ACCESS_PATH = '/api/v1'
ACCESS_SECONDS = 900
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
    if not digest:
        raise unauthenticated()
    # Join the user for every read: disabling or password-reset revocation is immediate.
    row = db.execute(select(AccountSession, AccountUser).join(AccountUser, AccountSession.user_id == AccountUser.id)
                     .where(AccountSession.access_hash == digest, AccountSession.revoked_at.is_(None),
                            AccountSession.access_expires_at > now, AccountSession.expires_at > now,
                            AccountSession.idle_expires_at > now, AccountUser.status == 'active',
                            AccountUser.email_verified_at.is_not(None))).first()
    if not row:
        raise unauthenticated()
    return row


def csrf_context(db, request, now, *, lock=False):
    digest = digest_or_none('csrf_context', request.cookies.get(CSRF_COOKIE))
    query = select(AccountCsrfContext).where(AccountCsrfContext.token_hash == digest,
                                            AccountCsrfContext.expires_at > now)
    if lock:
        query = query.with_for_update()
    context = db.scalar(query) if digest else None
    supplied = request.headers.get('X-CSRF-Token', '')
    if not context or len(supplied) > 64 or not secrets.compare_digest(context.csrf_token.encode(), supplied.encode()):
        raise csrf_invalid()
    if context.session_id is not None:
        try:
            session, _ = current_account(db, request, now)
        except AuthProblem:
            raise csrf_invalid() from None
        if context.session_id != session.id:
            raise csrf_invalid()
    return context


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
        # Bootstrap never trusts a guest credential. An expired access can obtain a
        # fresh anonymous context to log in again; it cannot become authenticated.
        try:
            session, _ = current_account(db, request, now)
            session_id = session.id
        except AuthProblem:
            session_id = None
        digest = digest_or_none('csrf_context', request.cookies.get(CSRF_COOKIE))
        context = db.scalar(select(AccountCsrfContext).where(AccountCsrfContext.token_hash == digest,
                            AccountCsrfContext.expires_at > now)) if digest else None
        if context and context.session_id == session_id:
            return CsrfRead(csrf_token=context.csrf_token)
        seconds = min(ANONYMOUS_CSRF_SECONDS, max(1, int((utc(session.access_expires_at)-now).total_seconds()))) if session_id else ANONYMOUS_CSRF_SECONDS
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

    app.include_router(router)
