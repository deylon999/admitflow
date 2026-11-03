"""Persist lookup budgets across API workers; no public codes or IP addresses."""
from alembic import op
import sqlalchemy as sa
revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('lookup_budgets',
        sa.Column('owner_hash', sa.String(64), sa.ForeignKey('browser_sessions.token_hash', ondelete='CASCADE'), primary_key=True),
        sa.Column('window_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used', sa.Integer(), nullable=False))


def downgrade():
    op.drop_table('lookup_budgets')
