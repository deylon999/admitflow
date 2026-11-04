"""Worker liveness and a run identifier that links a log line to its source check."""
from alembic import op
import sqlalchemy as sa
revision='0010'
down_revision='0009'
branch_labels=None
depends_on=None


def upgrade():
    op.create_table('worker_heartbeats',
        sa.Column('worker_id',sa.String(36),primary_key=True),
        sa.Column('started_at',sa.DateTime(timezone=True),nullable=False),
        sa.Column('last_seen_at',sa.DateTime(timezone=True),nullable=False),
        sa.Column('last_state',sa.String(16),nullable=False))
    with op.batch_alter_table('source_checks') as batch:
        batch.add_column(sa.Column('run_id',sa.String(36)))
    op.create_index('ix_source_checks_run','source_checks',['run_id'])


def downgrade():
    op.drop_index('ix_source_checks_run',table_name='source_checks')
    with op.batch_alter_table('source_checks') as batch:
        batch.drop_column('run_id')
    op.drop_table('worker_heartbeats')
