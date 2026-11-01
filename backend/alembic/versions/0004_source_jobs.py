"""Durable queue with fenced leases; no automatic source registration."""
from alembic import op
import sqlalchemy as sa

revision='0004'
down_revision='0003'
branch_labels=None
depends_on=None


def upgrade():
    op.create_table('source_jobs',
        sa.Column('source_id',sa.String(36),sa.ForeignKey('sources.id',ondelete='CASCADE'),primary_key=True),
        sa.Column('state',sa.String(16),nullable=False),
        sa.Column('next_run_at',sa.DateTime(timezone=True),nullable=False),
        sa.Column('lease_until',sa.DateTime(timezone=True),nullable=True),
        sa.Column('token',sa.String(36),nullable=True),
        sa.Column('attempts',sa.Integer(),nullable=False),
        sa.Column('max_attempts',sa.Integer(),nullable=False),
        sa.Column('interval_seconds',sa.Integer(),nullable=False),
        sa.Column('last_error_code',sa.String(80),nullable=True),
        sa.CheckConstraint("state IN ('queued','running','idle','failed')",name='job_state'),
        sa.CheckConstraint('attempts >= 0 AND attempts <= max_attempts AND max_attempts BETWEEN 1 AND 20',name='job_attempts'),
        sa.CheckConstraint('interval_seconds BETWEEN 60 AND 86400',name='job_interval'),
        sa.CheckConstraint("(state = 'running' AND token IS NOT NULL AND lease_until IS NOT NULL) OR (state != 'running' AND token IS NULL AND lease_until IS NULL)",name='job_lease'))
    op.create_index('ix_source_jobs_due','source_jobs',['state','next_run_at'])


def downgrade():
    op.drop_table('source_jobs')
