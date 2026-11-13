"""Independent account foundation; guest tables and rows are untouched."""
from alembic import op
import sqlalchemy as sa
revision = '0012'
down_revision = '0011'
branch_labels = None
depends_on = None

def _schema():
    metadata = sa.MetaData()
    sa.Table('account_rate_buckets', metadata,
        sa.Column('operation', sa.String(40), nullable=False, primary_key=True),
        sa.Column('subject_hash', sa.String(64), nullable=False, primary_key=True),
        sa.Column('window_start', sa.DateTime(timezone=True), nullable=False, primary_key=True),
        sa.Column('used', sa.Integer(), nullable=False, primary_key=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False, primary_key=False),
        sa.CheckConstraint('window_start < expires_at', name='account_rate_lifetime'),
        sa.CheckConstraint('used >= 0', name='account_rate_nonnegative'),
    )
    sa.Index('ix_account_rate_buckets_expires_at', metadata.tables['account_rate_buckets'].c.expires_at)
    sa.Table('account_users', metadata,
        sa.Column('id', sa.String(36), nullable=False, primary_key=True),
        sa.Column('email', sa.String(254), nullable=False, primary_key=False),
        sa.Column('password_hash', sa.String(512), nullable=False, primary_key=False),
        sa.Column('status', sa.String(16), nullable=False, primary_key=False),
        sa.Column('email_verified_at', sa.DateTime(timezone=True), nullable=True, primary_key=False),
        sa.Column('password_changed_at', sa.DateTime(timezone=True), nullable=False, primary_key=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, primary_key=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, primary_key=False),
        sa.UniqueConstraint('email'),
        sa.CheckConstraint('email = lower(trim(email)) AND length(email) BETWEEN 3 AND 254', name='account_email_normalized'),
        sa.CheckConstraint("status IN ('active', 'disabled')", name='account_user_status'),
    )
    sa.Table('account_action_tokens', metadata,
        sa.Column('token_hash', sa.String(64), nullable=False, primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('account_users.id', ondelete="CASCADE"), nullable=False, primary_key=False),
        sa.Column('purpose', sa.String(24), nullable=False, primary_key=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, primary_key=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False, primary_key=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True, primary_key=False),
        sa.CheckConstraint('created_at < expires_at', name='account_action_lifetime'),
        sa.CheckConstraint("purpose IN ('verify_email', 'reset_password')", name='account_action_purpose'),
    )
    sa.Index('ix_account_action_tokens_expires_at', metadata.tables['account_action_tokens'].c.expires_at)
    sa.Index('ix_account_action_tokens_user_id', metadata.tables['account_action_tokens'].c.user_id)
    sa.Table('account_sessions', metadata,
        sa.Column('id', sa.String(36), nullable=False, primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('account_users.id', ondelete="CASCADE"), nullable=False, primary_key=False),
        sa.Column('access_hash', sa.String(64), nullable=False, primary_key=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, primary_key=False),
        sa.Column('access_expires_at', sa.DateTime(timezone=True), nullable=False, primary_key=False),
        sa.Column('idle_expires_at', sa.DateTime(timezone=True), nullable=False, primary_key=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False, primary_key=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True, primary_key=False),
        sa.UniqueConstraint('access_hash'),
        sa.CheckConstraint('created_at < access_expires_at AND access_expires_at <= expires_at', name='account_access_lifetime'),
        sa.CheckConstraint('created_at < idle_expires_at AND idle_expires_at <= expires_at', name='account_idle_lifetime'),
    )
    sa.Index('ix_account_sessions_expires_at', metadata.tables['account_sessions'].c.expires_at)
    sa.Index('ix_account_sessions_user_id', metadata.tables['account_sessions'].c.user_id)
    sa.Table('account_csrf_contexts', metadata,
        sa.Column('token_hash', sa.String(64), nullable=False, primary_key=True),
        sa.Column('csrf_token', sa.String(64), nullable=False, primary_key=False),
        sa.Column('session_id', sa.String(36), sa.ForeignKey('account_sessions.id', ondelete="CASCADE"), nullable=True, primary_key=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, primary_key=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False, primary_key=False),
        sa.CheckConstraint('created_at < expires_at', name='account_csrf_lifetime'),
    )
    sa.Index('ix_account_csrf_contexts_expires_at', metadata.tables['account_csrf_contexts'].c.expires_at)
    sa.Index('ix_account_csrf_contexts_session_id', metadata.tables['account_csrf_contexts'].c.session_id)
    sa.Table('account_refresh_tokens', metadata,
        sa.Column('token_hash', sa.String(64), nullable=False, primary_key=True),
        sa.Column('session_id', sa.String(36), sa.ForeignKey('account_sessions.id', ondelete="CASCADE"), nullable=False, primary_key=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, primary_key=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False, primary_key=False),
        sa.Column('consumed_at', sa.DateTime(timezone=True), nullable=True, primary_key=False),
        sa.CheckConstraint('created_at < expires_at', name='account_refresh_lifetime'),
    )
    sa.Index('ix_account_refresh_tokens_session_id', metadata.tables['account_refresh_tokens'].c.session_id)
    return metadata


def upgrade():
    _schema().create_all(op.get_bind(), checkfirst=False)


def downgrade():
    # Only disposable databases: account deletion requires an explicit backup in production.
    _schema().drop_all(op.get_bind(), checkfirst=False)
