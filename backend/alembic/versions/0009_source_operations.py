"""Safe operator journal; no applicant identifiers, payloads or credentials."""
from alembic import op
import sqlalchemy as sa
revision='0009'
down_revision='0008'
branch_labels=None
depends_on=None

def upgrade():
    op.create_table('source_operations',sa.Column('id',sa.String(36),primary_key=True),
        sa.Column('source_id',sa.String(36),sa.ForeignKey('sources.id',ondelete='CASCADE'),nullable=False),
        sa.Column('action',sa.String(24),nullable=False),sa.Column('outcome',sa.String(24),nullable=False),
        sa.Column('adapter_version',sa.String(80)),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False))
    op.create_index('ix_source_operations_source_id','source_operations',['source_id'])

def downgrade():op.drop_table('source_operations')
