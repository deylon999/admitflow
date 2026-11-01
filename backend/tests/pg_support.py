"""Destructive tests own a newly created schema, never the shared/public schema."""
from contextlib import contextmanager
from uuid import uuid4

from sqlalchemy.engine import make_url
from sqlalchemy.schema import CreateSchema, DropSchema

from app.database import make_engine


def disposable_postgres_url(value):
    try:
        url = make_url(value)
        valid = url.get_backend_name() == 'postgresql' and (url.database or '').startswith('admitflow_test')
    except Exception:
        valid = False
    if not valid:
        raise ValueError('TEST_DATABASE_URL must name a disposable PostgreSQL admitflow_test* database') from None
    return url


@contextmanager
def isolated_postgres(value):
    url = disposable_postgres_url(value)
    admin = make_engine(url.render_as_string(hide_password=False))
    schema = f'admitflow_test_{uuid4().hex}'
    scoped, created = None, False
    try:
        with admin.begin() as db:
            db.execute(CreateSchema(schema))
        created = True
        scoped_url = url.update_query_dict({'options': f'-csearch_path={schema}'})
        scoped = make_engine(scoped_url.render_as_string(hide_password=False))
        yield scoped
    finally:
        try:
            if scoped is not None:
                scoped.dispose()
        finally:
            try:
                if created:
                    with admin.begin() as db:
                        db.execute(DropSchema(schema, cascade=True))
            finally:
                admin.dispose()
