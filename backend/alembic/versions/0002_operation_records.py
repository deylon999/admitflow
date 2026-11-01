"""Idempotent operations for manual watches."""
from alembic import op
from alembic import context
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
import sqlalchemy as sa
from app.migration_checks import checks_match

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def _table():
    metadata = sa.MetaData()
    sa.Table('browser_sessions', metadata, sa.Column('token_hash', sa.String(64), primary_key=True))
    sa.Table('watches', metadata, sa.Column('id', sa.String(36), primary_key=True))
    table = sa.Table('operation_records', metadata,
                    sa.Column('owner_hash', sa.String(64), nullable=False),
                    sa.Column('key', sa.String(100), nullable=False),
                    sa.Column('fingerprint', sa.String(64), nullable=False),
                    sa.Column('watch_id', sa.String(36), nullable=True),
                    sa.Column('response', sa.JSON(none_as_null=True), nullable=True),
                    sa.Column('response_status', sa.Integer(), nullable=False),
                    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
                    sa.PrimaryKeyConstraint('owner_hash', 'key'),
                    sa.ForeignKeyConstraint(['owner_hash'], ['browser_sessions.token_hash'], ondelete='CASCADE'),
                    sa.ForeignKeyConstraint(['watch_id'], ['watches.id'], ondelete='SET NULL'),
                    sa.CheckConstraint('(response_status = 201 AND response IS NOT NULL) OR (response_status = 410 AND response IS NULL)', name='operation_response_state'))
    sa.Index('ix_operation_records_watch_id', table.c.watch_id)
    return table


def upgrade():
    table = _table()
    if context.is_offline_mode():
        op.execute(sa.schema.CreateTable(table))
        for index in table.indexes:
            op.execute(sa.schema.CreateIndex(index))
        return
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table(table.name):
        include = lambda obj, name, kind, reflected, compare_to: kind != 'table' or name == table.name
        differences = compare_metadata(MigrationContext.configure(bind, opts={'include_object': include}), table.metadata)
        if any(not isinstance(change, tuple) or change[0] != 'add_index' for change in differences):
            raise RuntimeError('Existing operation_records differs from migration 0002')
        if not checks_match(bind, table) or inspector.get_pk_constraint(table.name)['constrained_columns'] != ['owner_hash', 'key']:
            raise RuntimeError('Existing operation_records has incompatible constraints')
    else:
        table.create(bind)
    for index in table.indexes:
        index.create(bind, checkfirst=True)


def downgrade():
    op.drop_table('operation_records')
