"""SQLAlchemy base and bounded engine creation."""

from sqlalchemy import create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


def make_engine(url: str):
    options = {'pool_pre_ping': True}
    if url.startswith('sqlite'):
        options['connect_args'] = {'check_same_thread': False}
        if url in ('sqlite://', 'sqlite:///:memory:'):
            options['poolclass'] = StaticPool
    elif make_url(url).get_backend_name() == 'postgresql':
        try:
            timeout = int(make_url(url).query.get('connect_timeout', '5'))
            if not 1 <= timeout <= 10:
                raise ValueError()
        except (ValueError, TypeError):
            raise ValueError('PostgreSQL connect_timeout must be between 1 and 10 seconds.') from None
        options['connect_args'] = {'connect_timeout': timeout}
        options['pool_timeout'] = 5
        # FastAPI runs sync routes on up to 40 threads; keep waits short and connections bounded.
        options['pool_size'] = 10
        options['max_overflow'] = 10
    engine = create_engine(url, **options)
    if url.startswith('sqlite'):
        @event.listens_for(engine, 'connect')
        def enable_foreign_keys(connection, _):
            connection.execute('PRAGMA foreign_keys=ON')
    return engine
