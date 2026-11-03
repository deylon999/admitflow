"""Make composite subscription FK agree with the simple cascading FK.

PostgreSQL can otherwise reject browser-session deletion before the other
subscription FK cascade executes. No domain rows or identifiers are rewritten.
"""
from alembic import op

revision='0005'
down_revision='0004'
branch_labels=None
depends_on=None


def replace_constraint(action):
    # assessments has no dependent tables. SQLite rebuilds only this child table;
    # PostgreSQL performs transactional DROP/ADD CONSTRAINT on the same rows.
    with op.batch_alter_table('assessments') as batch:
        batch.drop_constraint('fk_assessment_subscription_group',type_='foreignkey')
        batch.create_foreign_key('fk_assessment_subscription_group','subscriptions',
                                 ['subscription_id','group_id'],['id','group_id'],ondelete=action)


def upgrade():replace_constraint('CASCADE')


def downgrade():replace_constraint(None)
