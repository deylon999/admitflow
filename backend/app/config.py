import os
import re
from dataclasses import dataclass, field
from urllib.parse import urlsplit
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError


@dataclass(frozen=True)
class Settings:
    database_url: str = 'sqlite:///./abiturient.db'
    environment: str = 'development'
    secure_cookie: bool = False
    auto_create_schema: bool = True
    allowed_hosts: tuple[str, ...] = ('localhost','127.0.0.1','testserver')
    public_origin: str | None = None
    auth_enabled: bool = False
    auth_rate_key: str | None = field(default=None, repr=False)
    smtp_host: str | None = field(default=None, repr=False)
    smtp_port: int = 587
    smtp_username: str | None = field(default=None, repr=False)
    smtp_password: str | None = field(default=None, repr=False)
    smtp_from: str | None = field(default=None, repr=False)
    smtp_security: str = 'starttls'
    smtp_timeout_seconds: int = 5

    def __post_init__(self):
        if self.smtp_security not in ('starttls', 'ssl'):
            raise RuntimeError('SMTP_SECURITY must be starttls or ssl.')
        if type(self.smtp_port) is not int or not 1 <= self.smtp_port <= 65535:
            raise RuntimeError('SMTP_PORT must be1..65535.')
        if type(self.smtp_timeout_seconds) is not int or not 1 <= self.smtp_timeout_seconds <= 10:
            raise RuntimeError('SMTP_TIMEOUT_SECONDS must be1..10.')
        if any(value is not None for value in (self.smtp_host, self.smtp_username, self.smtp_password, self.smtp_from)):
            if (not isinstance(self.smtp_host, str) or len(self.smtp_host) > 253
                    or not re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?', self.smtp_host)):
                raise RuntimeError('SMTP_HOST must be an explicit hostname or IPv4 address.')
            for value in (self.smtp_username, self.smtp_password):
                if not isinstance(value, str) or not 1 <= len(value) <= 4096 or any(ord(c) < 32 or ord(c) == 127 for c in value):
                    raise RuntimeError('Configured SMTP requires valid username and password.')
            from .account_security import InvalidAccountInput, normalize_email
            try:
                normalize_email(self.smtp_from)
            except InvalidAccountInput:
                raise RuntimeError('SMTP_FROM must be a valid mailbox.') from None
            if not self.public_origin or not self.public_origin.startswith('https://'):
                raise RuntimeError('SMTP links require an explicit HTTPS PUBLIC_ORIGIN.')
        if type(self.auth_enabled) is not bool:
            raise RuntimeError('AUTH_ENABLED must be a boolean.')
        if self.auth_enabled and (not isinstance(self.auth_rate_key, str) or not 32 <= len(self.auth_rate_key.encode('utf-8')) <= 1024):
            raise RuntimeError('Enabled authentication requires AUTH_RATE_KEY of32..1024 UTF8 bytes.')
        if self.environment not in ('development','production'):
            raise RuntimeError('ENVIRONMENT must be development or production.')
        if type(self.secure_cookie) is not bool or type(self.auto_create_schema) is not bool:
            raise RuntimeError('Cookie/schema settings must be booleans.')
        if not self.allowed_hosts or any(not re.fullmatch(r'[a-z0-9](?:[a-z0-9.-]{0,252}[a-z0-9])?', host) for host in self.allowed_hosts):
            raise RuntimeError('ALLOWED_HOSTS must contain exact hostnames without wildcards or ports.')
        if self.public_origin:
            try:
                origin = urlsplit(self.public_origin)
                valid = (origin.scheme in ('http','https') and origin.hostname in self.allowed_hosts
                         and not origin.username and not origin.password and not origin.path
                         and not origin.query and not origin.fragment and origin.port != 0)
            except ValueError:
                valid = False
            if not valid:
                raise RuntimeError('PUBLIC_ORIGIN must be an origin matching ALLOWED_HOSTS.')
        if self.environment == 'production' and (not self.public_origin or not self.public_origin.startswith('https://')):
            raise RuntimeError('Production requires an explicit HTTPS PUBLIC_ORIGIN.')
        if self.environment == 'production':
            try:
                backend = make_url(self.database_url).get_backend_name()
            except (ArgumentError, ValueError):
                raise RuntimeError('Invalid DATABASE_URL.') from None
            if backend != 'postgresql' or not self.secure_cookie:
                raise RuntimeError('Production requires PostgreSQL and SECURE_COOKIE=true (HTTPS).')
            if self.auto_create_schema:
                raise RuntimeError('Production requires explicit migrations, not AUTO_CREATE_SCHEMA=true.')

    @classmethod
    def from_env(cls):
        environment = os.getenv('ENVIRONMENT', 'development')
        if environment not in ('development','production'):
            raise RuntimeError('ENVIRONMENT must be development or production.')
        production = environment == 'production'
        def boolean(name,default):
            value=os.getenv(name,default).lower()
            if value not in ('true','false'):
                raise RuntimeError(f'{name} must be true or false.')
            return value=='true'
        def integer(name, default):
            try:
                return int(os.getenv(name, str(default)))
            except ValueError:
                raise RuntimeError(f'{name} must be an integer.') from None
        secure=boolean('SECURE_COOKIE','true' if production else 'false')
        auto=boolean('AUTO_CREATE_SCHEMA','false' if production else 'true')
        config = cls(
            database_url=os.getenv('DATABASE_URL', 'sqlite:///./abiturient.db'),
            environment='production' if production else 'development',
            secure_cookie=secure,
            auto_create_schema=auto,
            allowed_hosts=tuple(host.strip().lower() for host in os.getenv('ALLOWED_HOSTS','' if production else 'localhost,127.0.0.1,testserver').split(',') if host.strip()),
            public_origin=os.getenv('PUBLIC_ORIGIN') or None,
            auth_enabled=boolean('AUTH_ENABLED', 'false'),
            auth_rate_key=os.getenv('AUTH_RATE_KEY') or None,
            smtp_host=os.getenv('SMTP_HOST') or None,
            smtp_port=integer('SMTP_PORT', 465 if os.getenv('SMTP_SECURITY') == 'ssl' else 587),
            smtp_username=os.getenv('SMTP_USERNAME') or None,
            smtp_password=os.getenv('SMTP_PASSWORD') or None,
            smtp_from=os.getenv('SMTP_FROM') or None,
            smtp_security=os.getenv('SMTP_SECURITY', 'starttls'),
            smtp_timeout_seconds=integer('SMTP_TIMEOUT_SECONDS', 5),
        )
        return config
