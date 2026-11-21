"""Bounded account input and standard Argon2id. No HTTP or guest side effects."""
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import re
import secrets
from threading import BoundedSemaphore

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from argon2.profiles import RFC_9106_LOW_MEMORY

_HASHER = PasswordHasher.from_parameters(RFC_9106_LOW_MEMORY)
_HASH_SLOTS = BoundedSemaphore(2)
# Used for nonexistent accounts as well; never a valid account credential.
_DUMMY_HASH = _HASHER.hash(secrets.token_urlsafe(32))
_COMMON_PASSWORDS = frozenset({
    'password', 'password123', 'password123456789', '123456789012345',
    '1234567890123456', 'qwertyuiopasdfgh', 'iloveyou', 'letmein',
})
_LOCAL = re.compile(r"[a-z0-9!#$%&'*+/=?^_`{|}~.-]+", re.ASCII)
_LABEL = re.compile(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?', re.ASCII)
_TOKEN = re.compile(r'[A-Za-z0-9_-]{43}', re.ASCII)
_PURPOSES = frozenset({'access', 'refresh', 'verify_email', 'reset_password', 'csrf_context'})


class InvalidAccountInput(ValueError):
    """Messages must never interpolate the supplied input."""


class PasswordCapacityError(RuntimeError):
    pass


@contextmanager
def _hash_slot():
    if not _HASH_SLOTS.acquire(blocking=False):
        raise PasswordCapacityError('Password verification capacity exceeded.')
    try:
        yield
    finally:
        _HASH_SLOTS.release()


def normalize_email(value: str) -> str:
    if not isinstance(value, str) or len(value) > 320 or not value.isascii():
        raise InvalidAccountInput('Некорректный email.')
    value = value.strip().lower()
    if len(value) > 254 or value.count('@') != 1:
        raise InvalidAccountInput('Некорректный email.')
    local, domain = value.split('@')
    labels = domain.split('.')
    if (not 1 <= len(local) <= 64 or not _LOCAL.fullmatch(local)
            or local.startswith('.') or local.endswith('.') or '..' in local
            or len(labels) < 2 or not all(_LABEL.fullmatch(label) for label in labels)
            or labels[-1].isdigit()):
        raise InvalidAccountInput('Некорректный email.')
    return value


def _bounded_password(value: str):
    if not isinstance(value, str) or not 1 <= len(value) <= 128 or '\0' in value:
        raise InvalidAccountInput('Пароль должен содержать от 15 до 128 символов.')
    try:
        if len(value.encode('utf-8')) > 512:
            raise ValueError()
    except (UnicodeError, ValueError):
        raise InvalidAccountInput('Некорректный формат пароля.') from None


def validate_password(value: str) -> None:
    _bounded_password(value)
    if len(value) < 15:
        raise InvalidAccountInput('Пароль должен содержать от 15 до 128 символов.')
    if value.casefold() in _COMMON_PASSWORDS:
        raise InvalidAccountInput('Выберите менее распространённый пароль.')


def hash_password(value: str) -> str:
    validate_password(value)
    with _hash_slot():
        return _HASHER.hash(value)


@dataclass(frozen=True)
class PasswordCheck:
    valid: bool
    needs_rehash: bool = False


def verify_password(value: str, encoded: str | None) -> PasswordCheck:
    _bounded_password(value)  # Login checks size, not the current registration policy.
    with _hash_slot():
        try:
            valid = _HASHER.verify(encoded if encoded is not None else _DUMMY_HASH, value)
            return PasswordCheck(valid=valid and encoded is not None,
                                 needs_rehash=encoded is not None and _HASHER.check_needs_rehash(encoded))
        except (VerificationError, InvalidHashError):
            return PasswordCheck(False)


def new_token() -> str:
    return secrets.token_urlsafe(32)


def credential_digest(purpose: str, token: str) -> str:
    if purpose not in _PURPOSES or not isinstance(token, str) or not _TOKEN.fullmatch(token):
        raise InvalidAccountInput('Недействительный токен.')
    return hashlib.sha256(f'admitflow-account-v1:{purpose}:{token}'.encode('ascii')).hexdigest()
