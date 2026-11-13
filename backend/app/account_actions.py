"""Single-use email actions. DB mutations serialize under the stable user row."""
from datetime import timedelta

from sqlalchemy import select, update

from .accounts import AccountActionToken, AccountRefreshToken, AccountSession, AccountUser
from .account_security import credential_digest, new_token


class InvalidActionToken(ValueError):
    def __init__(self):
        super().__init__('Ссылка недействительна или срок её действия истёк. Запросите новую.')


def _lock_user(db, user_id):
    user = db.scalar(select(AccountUser).where(AccountUser.id == user_id).with_for_update()
                     .execution_options(populate_existing=True))
    if not user:
        raise InvalidActionToken()
    return user


def action_identity(db, purpose, raw_token):
    digest = credential_digest(purpose, raw_token)
    user_id = db.scalar(select(AccountActionToken.user_id).where(AccountActionToken.token_hash == digest,
                         AccountActionToken.purpose == purpose))
    if not user_id:
        raise InvalidActionToken()
    return user_id, digest


def _active_action(db, user_id, purpose, digest, now):
    token = db.scalar(select(AccountActionToken).where(AccountActionToken.token_hash == digest,
                      AccountActionToken.user_id == user_id, AccountActionToken.purpose == purpose,
                      AccountActionToken.used_at.is_(None), AccountActionToken.expires_at > now)
                      .with_for_update().execution_options(populate_existing=True))
    if not token:
        raise InvalidActionToken()
    return token


def issue_action(db, email, purpose, clock):
    user_id = db.scalar(select(AccountUser.id).where(AccountUser.email == email))
    if not user_id:
        db.rollback(); return None
    user = db.scalar(select(AccountUser).where(AccountUser.id == user_id, AccountUser.email == email)
                     .with_for_update().execution_options(populate_existing=True))
    if not user:
        db.rollback(); return None
    eligible = (user.status == 'active' and ((purpose == 'verify_email' and user.email_verified_at is None)
                 or (purpose == 'reset_password' and user.email_verified_at is not None)))
    if not eligible:
        db.rollback(); return None
    now = clock()
    db.execute(update(AccountActionToken).where(AccountActionToken.user_id == user.id,
               AccountActionToken.purpose == purpose, AccountActionToken.used_at.is_(None))
               .values(used_at=now).execution_options(synchronize_session=False))
    raw_token = new_token()
    db.add(AccountActionToken(token_hash=credential_digest(purpose, raw_token), user_id=user.id,
                              purpose=purpose, created_at=now,
                              expires_at=now+timedelta(hours=24) if purpose == 'verify_email' else now+timedelta(minutes=30)))
    db.commit()  # Caller sends outside the transaction; no raw token is persisted.
    return raw_token


def confirm_verification(db, identity, clock, check_csrf):
    user_id, digest = identity
    user = _lock_user(db, user_id)
    now = clock()
    _active_action(db, user_id, 'verify_email', digest, now)
    if user.status != 'active' or user.email_verified_at is not None:
        raise InvalidActionToken()
    check_csrf(now)
    user.email_verified_at = now; user.updated_at = now
    db.execute(update(AccountActionToken).where(AccountActionToken.user_id == user_id,
               AccountActionToken.purpose == 'verify_email', AccountActionToken.used_at.is_(None))
               .values(used_at=now).execution_options(synchronize_session=False))
    db.commit()


def confirm_reset(db, identity, encoded_password, clock, check_csrf):
    user_id, digest = identity
    user = _lock_user(db, user_id)
    sessions = db.scalars(select(AccountSession).where(AccountSession.user_id == user_id)
                          .order_by(AccountSession.id).with_for_update()
                          .execution_options(populate_existing=True)).all()
    now = clock()
    _active_action(db, user_id, 'reset_password', digest, now)
    if user.status != 'active' or user.email_verified_at is None:
        raise InvalidActionToken()
    # CSRF is immutable proof, not modified here. Do not lock or bulk-update a
    # foreign account's context: cross-account reset requests could otherwise form
    # a cycle through the other request's CSRF row. Revoked sessions deny all auth.
    check_csrf(now)
    user.password_hash = encoded_password
    user.password_changed_at = now; user.updated_at = now
    for session in sessions:
        if session.revoked_at is None: session.revoked_at = now
    db.execute(update(AccountRefreshToken).where(
               AccountRefreshToken.session_id.in_(select(AccountSession.id).where(AccountSession.user_id == user_id)),
               AccountRefreshToken.consumed_at.is_(None)).values(consumed_at=now)
               .execution_options(synchronize_session=False))
    db.execute(update(AccountActionToken).where(AccountActionToken.user_id == user_id,
               AccountActionToken.used_at.is_(None)).values(used_at=now)
               .execution_options(synchronize_session=False))
    db.commit()
