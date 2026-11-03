"""Retain bounded-safe source outcomes after recovery, without raw or identifiers."""
from alembic import op
import sqlalchemy as sa
revision='0007'
down_revision='0006'
branch_labels=None
depends_on=None


def upgrade():
    op.create_table('source_checks',
        sa.Column('id',sa.String(36),primary_key=True),
        sa.Column('source_id',sa.String(36),sa.ForeignKey('sources.id',ondelete='CASCADE'),nullable=False),
        sa.Column('checked_at',sa.DateTime(timezone=True),nullable=False),
        sa.Column('outcome',sa.String(16),nullable=False),
        sa.Column('error_code',sa.String(80)),
        sa.Column('snapshot_id',sa.String(36),sa.ForeignKey('source_snapshots.id',ondelete='RESTRICT')),
        sa.CheckConstraint("outcome IN ('success','failed')",name='source_check_outcome'))
    op.create_index('ix_source_checks_time','source_checks',['source_id','checked_at'])


def downgrade():
    op.drop_table('source_checks')
