"""Initial schema, frozen independently of future application models."""
import re
from alembic import context, op
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
import sqlalchemy as sa

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def _index(metadata, name, table_name, columns, unique=False):
    sa.Index(name, *(metadata.tables[table_name].c[name] for name in columns), unique=unique)


def _schema():
    metadata = sa.MetaData()
    sa.Table('browser_sessions', metadata,
    sa.Column('token_hash', sa.String(length=64), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('token_hash')
    )
    _index(metadata, str('ix_browser_sessions_expires_at'), 'browser_sessions', ['expires_at'], unique=False)
    sa.Table('universities', metadata,
    sa.Column('id', sa.String(length=80), nullable=False),
    sa.Column('name', sa.String(length=300), nullable=False),
    sa.Column('region', sa.String(length=120), nullable=True),
    sa.Column('parent_id', sa.String(length=80), nullable=True),
    sa.Column('official_url', sa.String(length=2048), nullable=False),
    sa.Column('provenance_url', sa.String(length=2048), nullable=False),
    sa.Column('verified_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['parent_id'], ['universities.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id')
    )
    sa.Table('campaigns', metadata,
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('university_id', sa.String(length=80), nullable=False),
    sa.Column('year', sa.Integer(), nullable=False),
    sa.Column('level', sa.String(length=24), nullable=False),
    sa.CheckConstraint("level IN ('bachelor', 'specialist', 'master')", name='campaign_level'),
    sa.CheckConstraint('year >= 2000 AND year <= 2100', name='campaign_year'),
    sa.ForeignKeyConstraint(['university_id'], ['universities.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('university_id', 'year', 'level', name='uq_campaign_identity')
    )
    sa.Table('watches', metadata,
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('owner_hash', sa.String(length=64), nullable=False),
    sa.Column('university', sa.String(length=160), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('source_url', sa.String(length=2048), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['owner_hash'], ['browser_sessions.token_hash'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    _index(metadata, str('ix_watches_owner_hash'), 'watches', ['owner_hash'], unique=False)
    sa.Table('competition_groups', metadata,
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('campaign_id', sa.String(length=36), nullable=False),
    sa.Column('official_id', sa.String(length=160), nullable=False),
    sa.Column('title', sa.String(length=300), nullable=False),
    sa.Column('study_form', sa.String(length=40), nullable=False),
    sa.Column('funding', sa.String(length=40), nullable=False),
    sa.Column('category', sa.String(length=80), nullable=False),
    sa.Column('seats', sa.Integer(), nullable=True),
    sa.Column('coverage', sa.String(length=24), nullable=False),
    sa.Column('rules_version', sa.String(length=80), nullable=True),
    sa.CheckConstraint("coverage != 'automatic' OR rules_version IS NOT NULL", name='automatic_requires_rules'),
    sa.CheckConstraint("coverage IN ('candidate', 'manual', 'automatic', 'suspended')", name='group_coverage'),
    sa.CheckConstraint('seats IS NULL OR seats >= 0', name='group_seats'),
    sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('campaign_id', 'official_id', name='uq_group_identity')
    )
    sa.Table('snapshots', metadata,
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('watch_id', sa.String(length=36), nullable=False),
    sa.Column('captured_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('rank', sa.Integer(), nullable=False),
    sa.Column('seats', sa.Integer(), nullable=False),
    sa.Column('excluded', sa.Integer(), nullable=False),
    sa.Column('no_consent', sa.Integer(), nullable=False),
    sa.Column('source_kind', sa.String(length=24), nullable=False),
    sa.Column('model_version', sa.String(length=32), nullable=False),
    sa.CheckConstraint('excluded >= 0 AND no_consent >= 0 AND excluded + no_consent < rank', name='groups_above'),
    sa.CheckConstraint('rank >= 1 AND rank <= 1000000', name='rank_range'),
    sa.CheckConstraint('seats >= 1 AND seats <= 1000000', name='seats_range'),
    sa.ForeignKeyConstraint(['watch_id'], ['watches.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    _index(metadata, 'ix_snapshots_watch_time', 'snapshots', ['watch_id', 'captured_at'], unique=False)
    sa.Table('sources', metadata,
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('group_id', sa.String(length=36), nullable=False),
    sa.Column('url', sa.String(length=2048), nullable=False),
    sa.Column('domain', sa.String(length=255), nullable=False),
    sa.Column('adapter_version', sa.String(length=80), nullable=True),
    sa.Column('enabled', sa.Boolean(), nullable=False),
    sa.Column('last_checked_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_success_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_error_code', sa.String(length=80), nullable=True),
    sa.CheckConstraint('NOT enabled OR adapter_version IS NOT NULL', name='enabled_source_has_adapter'),
    sa.ForeignKeyConstraint(['group_id'], ['competition_groups.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id', 'group_id', name='uq_source_group')
    )
    _index(metadata, str('ix_sources_group_id'), 'sources', ['group_id'], unique=False)
    sa.Table('subscriptions', metadata,
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('owner_hash', sa.String(length=64), nullable=False),
    sa.Column('group_id', sa.String(length=36), nullable=False),
    sa.Column('candidate_key', sa.String(length=100), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['group_id'], ['competition_groups.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['owner_hash'], ['browser_sessions.token_hash'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id', 'group_id', name='uq_subscription_group'),
    sa.UniqueConstraint('owner_hash', 'group_id', 'candidate_key', name='uq_subscription')
    )
    _index(metadata, str('ix_subscriptions_owner_hash'), 'subscriptions', ['owner_hash'], unique=False)
    sa.Table('source_snapshots', metadata,
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('source_id', sa.String(length=36), nullable=False),
    sa.Column('group_id', sa.String(length=36), nullable=False),
    sa.Column('payload_hash', sa.String(length=64), nullable=False),
    sa.Column('fetched_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('source_updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('kind', sa.String(length=16), nullable=False),
    sa.Column('row_count', sa.Integer(), nullable=False),
    sa.Column('complete', sa.Boolean(), nullable=False),
    sa.CheckConstraint("kind IN ('live', 'archive')", name='snapshot_kind'),
    sa.CheckConstraint('row_count >= 0', name='snapshot_rows'),
    sa.ForeignKeyConstraint(['group_id'], ['competition_groups.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['source_id', 'group_id'], ['sources.id', 'sources.group_id'], name='fk_snapshot_source_group'),
    sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id', 'group_id', name='uq_snapshot_group'),
    sa.UniqueConstraint('source_id', 'id', name='uq_source_snapshot_id'),
    sa.UniqueConstraint('source_id', 'payload_hash', name='uq_source_payload')
    )
    sa.Table('assessments', metadata,
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('subscription_id', sa.String(length=36), nullable=False),
    sa.Column('group_id', sa.String(length=36), nullable=False),
    sa.Column('snapshot_id', sa.String(length=36), nullable=False),
    sa.Column('rules_version', sa.String(length=80), nullable=False),
    sa.Column('assessed_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('state', sa.String(length=32), nullable=False),
    sa.Column('facts', sa.JSON(), nullable=False),
    sa.Column('assumptions', sa.JSON(), nullable=False),
    sa.CheckConstraint("state IN ('within', 'conditional', 'out', 'unsupported', 'insufficient_data')", name='assessment_state'),
    sa.ForeignKeyConstraint(['group_id'], ['competition_groups.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['snapshot_id', 'group_id'], ['source_snapshots.id', 'source_snapshots.group_id'], name='fk_assessment_snapshot_group'),
    sa.ForeignKeyConstraint(['snapshot_id'], ['source_snapshots.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['subscription_id', 'group_id'], ['subscriptions.id', 'subscriptions.group_id'], name='fk_assessment_subscription_group'),
    sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('subscription_id', 'snapshot_id', 'rules_version', name='uq_assessment')
    )
    sa.Table('candidate_entries', metadata,
    sa.Column('snapshot_id', sa.String(length=36), nullable=False),
    sa.Column('candidate_key', sa.String(length=100), nullable=False),
    sa.Column('official_rank', sa.Integer(), nullable=False),
    sa.Column('score', sa.Numeric(precision=8, scale=2), nullable=True),
    sa.Column('consent', sa.Boolean(), nullable=True),
    sa.Column('priority', sa.Integer(), nullable=True),
    sa.Column('participation', sa.String(length=24), nullable=False),
    sa.CheckConstraint("participation IN ('unknown', 'active', 'withdrawn', 'enrolled')", name='entry_participation'),
    sa.CheckConstraint('official_rank > 0', name='entry_rank'),
    sa.CheckConstraint('priority IS NULL OR priority > 0', name='entry_priority'),
    sa.ForeignKeyConstraint(['snapshot_id'], ['source_snapshots.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('snapshot_id', 'candidate_key'),
    sa.UniqueConstraint('snapshot_id', 'official_rank', name='uq_snapshot_rank')
    )
    sa.Table('published_snapshots', metadata,
    sa.Column('source_id', sa.String(length=36), nullable=False),
    sa.Column('snapshot_id', sa.String(length=36), nullable=False),
    sa.ForeignKeyConstraint(['snapshot_id'], ['source_snapshots.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['source_id', 'snapshot_id'], ['source_snapshots.source_id', 'source_snapshots.id'], name='fk_published_source_snapshot'),
    sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('source_id')
    )
    return metadata


def _validate_existing(bind, metadata):
    # Adopt only identical tables (old development create_all databases).
    # Never stamp over changed columns, foreign keys or unexpected tables.
    differences = compare_metadata(MigrationContext.configure(bind), metadata)
    if any(not isinstance(change, tuple) or change[0] not in ('add_table', 'add_index') for change in differences):
        raise RuntimeError('Existing database differs from the initial schema. Back up and inspect it before migration.')
    inspector = sa.inspect(bind)
    existing = set(inspector.get_table_names())
    normalise = lambda value: re.sub(r'\s+', '', value).lower()
    for table in metadata.tables.values():
        if table.name not in existing:
            continue
        expected_pk = [column.name for column in table.primary_key.columns]
        if inspector.get_pk_constraint(table.name)['constrained_columns'] != expected_pk:
            raise RuntimeError(f'Unexpected primary key in {table.name}')
        actual_checks = {normalise(item['sqltext']) for item in inspector.get_check_constraints(table.name)}
        expected_checks = {normalise(str(item.sqltext)) for item in table.constraints if isinstance(item, sa.CheckConstraint)}
        if actual_checks != expected_checks:
            raise RuntimeError(f'Unexpected check constraints in {table.name}')


def upgrade():
    metadata = _schema()
    bind = op.get_bind()
    if context.is_offline_mode():
        for table in metadata.sorted_tables:
            op.execute(sa.schema.CreateTable(table))
            for index in table.indexes:
                op.execute(sa.schema.CreateIndex(index))
        return
    _validate_existing(bind, metadata)
    metadata.create_all(bind)
    for table in metadata.tables.values():
        for index in table.indexes:
            index.create(bind, checkfirst=True)


def downgrade():
    metadata = _schema()
    if context.is_offline_mode():
        for table in reversed(metadata.sorted_tables):
            op.execute(sa.schema.DropTable(table))
    else:
        metadata.drop_all(op.get_bind())
