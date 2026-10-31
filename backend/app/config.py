import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str = 'sqlite:///./abiturient.db'
    environment: str = 'development'
    secure_cookie: bool = False
    auto_create_schema: bool = True

    @classmethod
    def from_env(cls):
        production = os.getenv('ENVIRONMENT', 'development') == 'production'
        config = cls(
            database_url=os.getenv('DATABASE_URL', 'sqlite:///./abiturient.db'),
            environment='production' if production else 'development',
            secure_cookie=os.getenv('SECURE_COOKIE', 'true' if production else 'false').lower() == 'true',
            auto_create_schema=not production and os.getenv('AUTO_CREATE_SCHEMA', 'true').lower() == 'true',
        )
        if production and (config.database_url.startswith('sqlite') or not config.secure_cookie):
            raise RuntimeError('Production requires PostgreSQL and SECURE_COOKIE=true (HTTPS).')
        return config
