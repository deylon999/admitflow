"""Versioned imports; existing unversioned snapshots remain explicitly unknown."""
from alembic import op
import sqlalchemy as sa

revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('sources',sa.Column('snapshot_kind',sa.String(16),nullable=False,server_default='archive'))
    op.add_column('candidate_entries',sa.Column('row_ref',sa.String(100),nullable=True))
    # PostgreSQL emits ALTER TABLE. SQLite uses a transactional batch rebuild.
    with op.batch_alter_table('source_snapshots') as batch:
        for name,kind in [('adapter_version',sa.String(80)),('normalized_hash',sa.String(64)),('seats',sa.Integer()),('warnings',sa.JSON()),('fetched_url',sa.String(2048)),('content_type',sa.String(100)),('charset',sa.String(80))]:
            batch.add_column(sa.Column(name,kind,nullable=True))
        batch.drop_constraint('uq_source_payload',type_='unique')
        batch.create_unique_constraint('uq_source_payload_version',['source_id','payload_hash','adapter_version'])


def downgrade():
    # Destructive downgrade cannot collapse multiple parser versions of one raw.
    with op.batch_alter_table('source_snapshots') as batch:
        batch.drop_constraint('uq_source_payload_version',type_='unique')
        batch.create_unique_constraint('uq_source_payload',['source_id','payload_hash'])
        for name in ['adapter_version','normalized_hash','seats','warnings','fetched_url','content_type','charset']:
            batch.drop_column(name)
    op.drop_column('candidate_entries','row_ref')
    op.drop_column('sources','snapshot_kind')
