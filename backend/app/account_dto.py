from datetime import datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, Field, SecretStr

from .account_security import normalize_email, validate_password
from .schema_base import CamelModel


def registration_password(value: SecretStr):
    validate_password(value.get_secret_value())
    return value


Email = Annotated[str, Field(strict=True, min_length=3, max_length=320), AfterValidator(normalize_email)]
Password = Annotated[SecretStr, Field(min_length=1, max_length=128)]


class RegistrationRequest(CamelModel):
    email: Email
    password: Annotated[Password, AfterValidator(registration_password)]


class LoginRequest(CamelModel):
    email: Email
    password: Password


class AccountRead(CamelModel):
    id: str
    email: str
    email_verified: Literal[True] = True


class AccountSessionRead(CamelModel):
    account: AccountRead
    access_expires_at: datetime
    absolute_expires_at: datetime


class CsrfRead(CamelModel):
    csrf_token: str


class EmptyAuthRequest(CamelModel):
    pass


class RegistrationRead(CamelModel):
    message: str = 'Запрос принят. Если регистрация доступна, проверьте почту.'
