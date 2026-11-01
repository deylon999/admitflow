from pathlib import Path

from alembic import command
from alembic.config import Config


def ensure_restore_complete(engine):
    if engine.dialect.name=='sqlite' and engine.url.database not in (None,'',':memory:'):
        marker=Path(engine.url.database).resolve().parent/'restore.pending'
        if marker.exists() or marker.is_symlink():
            raise RuntimeError('Database restore is incomplete; inspect it and restore into a new directory.')


def upgrade_schema(engine):
    ensure_restore_complete(engine)
    config = Config(str(Path(__file__).resolve().parents[1]/'alembic.ini'))
    with engine.connect() as connection:
        config.attributes['connection'] = connection
        command.upgrade(config,'head')
