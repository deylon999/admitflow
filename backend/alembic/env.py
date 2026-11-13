from app import accounts  # Register independent account metadata.
from alembic import context

from app import admissions  # Register the complete target schema.
from app import jobs
from app import observability  # Register worker_heartbeats for standalone Alembic.
from app.config import Settings
from app.database import Base, make_engine

settings = Settings.from_env()

if context.is_offline_mode():
    context.configure(url=settings.database_url, target_metadata=Base.metadata, literal_binds=True, dialect_opts={'paramstyle': 'named'})
    with context.begin_transaction():
        context.run_migrations()
else:
    supplied = context.config.attributes.get('connection')
    engine = None if supplied is not None else make_engine(settings.database_url)
    connection = supplied if supplied is not None else engine.connect()
    try:
        if connection.dialect.name == 'sqlite':
            # Batch rebuilds need FK checks suspended on this migration-only connection.
            connection.exec_driver_sql('PRAGMA foreign_keys=OFF')
            connection.commit()
        context.configure(connection=connection, target_metadata=Base.metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()
            if connection.dialect.name == 'sqlite' and connection.exec_driver_sql('PRAGMA foreign_key_check').first():
                raise RuntimeError('Migration violates foreign keys')
        connection.commit()
    finally:
        if connection.dialect.name == 'sqlite':
            connection.rollback()
            connection.exec_driver_sql('PRAGMA foreign_keys=ON')
            connection.commit()
        if supplied is None:
            connection.close()
            engine.dispose()
