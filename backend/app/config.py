import os
import re
from dataclasses import dataclass
from urllib.parse import urlsplit


@dataclass(frozen=True)
class Settings:
    database_url: str = 'sqlite:///./abiturient.db'
    environment: str = 'development'
    secure_cookie: bool = False
    auto_create_schema: bool = True
    allowed_hosts: tuple[str, ...] = ('localhost','127.0.0.1','testserver')
    public_origin: str | None = None

    def __post_init__(self):
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

    @classmethod
    def from_env(cls):
        production = os.getenv('ENVIRONMENT', 'development') == 'production'
        config = cls(
            database_url=os.getenv('DATABASE_URL', 'sqlite:///./abiturient.db'),
            environment='production' if production else 'development',
            secure_cookie=os.getenv('SECURE_COOKIE', 'true' if production else 'false').lower() == 'true',
            auto_create_schema=not production and os.getenv('AUTO_CREATE_SCHEMA', 'true').lower() == 'true',
            allowed_hosts=tuple(host.strip().lower() for host in os.getenv('ALLOWED_HOSTS','' if production else 'localhost,127.0.0.1,testserver').split(',') if host.strip()),
            public_origin=os.getenv('PUBLIC_ORIGIN') or None,
        )
        if production and (config.database_url.startswith('sqlite') or not config.secure_cookie):
            raise RuntimeError('Production requires PostgreSQL and SECURE_COOKIE=true (HTTPS).')
        return config
