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

    def __post_init__(self):
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
        )
        return config
