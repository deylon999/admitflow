"""Owner-scoped scenario changes through cascading assessment references."""
from alembic import op
import sqlalchemy as sa
revision='0008'
down_revision='0007'
branch_labels=None
depends_on=None


def upgrade():
    op.create_table('change_events',sa.Column('id',sa.String(36),primary_key=True),
        sa.Column('assessment_id',sa.String(36),sa.ForeignKey('assessments.id',ondelete='CASCADE'),nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('seen_at',sa.DateTime(timezone=True)))
    op.create_index('ix_change_events_assessment_id','change_events',['assessment_id'],unique=True)


def downgrade():op.drop_table('change_events')
