"""Add programme identity and M:N competition links, preserving all legacy IDs.

No backfill: a competition group is not proof of a distinct programme.
"""
from alembic import op
import sqlalchemy as sa

revision = '0013'
down_revision = '0012'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('campaigns') as batch:
        batch.create_unique_constraint('uq_campaign_program_scope', ['id', 'university_id', 'level'])
    with op.batch_alter_table('competition_groups') as batch:
        batch.create_unique_constraint('uq_group_campaign_scope', ['id', 'campaign_id'])
    op.create_table('programs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('university_id', sa.String(80), nullable=False),
        sa.Column('level', sa.String(24), nullable=False),
        sa.Column('origin_campaign_id', sa.String(36), nullable=False),
        sa.Column('source_namespace', sa.String(160), nullable=False),
        sa.Column('source_key', sa.String(300), nullable=False),
        sa.UniqueConstraint('origin_campaign_id', 'source_namespace', 'source_key', name='uq_program_origin_identity'),
        sa.UniqueConstraint('id', 'university_id', 'level', name='uq_program_scope'),
        sa.ForeignKeyConstraint(['origin_campaign_id', 'university_id', 'level'],
                                ['campaigns.id', 'campaigns.university_id', 'campaigns.level'],
                                name='fk_program_origin_scope', ondelete='RESTRICT'),
        sa.CheckConstraint("level IN ('bachelor', 'specialist')", name='program_level'),
        sa.CheckConstraint('length(trim(source_namespace)) > 0 AND length(trim(source_key)) > 0', name='program_source_identity'),
    )
    op.create_table('campaign_programs',
        sa.Column('program_id', sa.String(36), primary_key=True),
        sa.Column('campaign_id', sa.String(36), primary_key=True),
        sa.Column('university_id', sa.String(80), nullable=False),
        sa.Column('level', sa.String(24), nullable=False),
        sa.ForeignKeyConstraint(['program_id', 'university_id', 'level'],
                                ['programs.id', 'programs.university_id', 'programs.level'],
                                name='fk_campaign_program_scope', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['campaign_id', 'university_id', 'level'],
                                ['campaigns.id', 'campaigns.university_id', 'campaigns.level'],
                                name='fk_program_campaign_scope', ondelete='RESTRICT'),
    )
    op.create_table('competition_group_programs',
        sa.Column('group_id', sa.String(36), primary_key=True),
        sa.Column('program_id', sa.String(36), primary_key=True),
        sa.Column('campaign_id', sa.String(36), nullable=False),
        sa.ForeignKeyConstraint(['group_id', 'campaign_id'],
                                ['competition_groups.id', 'competition_groups.campaign_id'],
                                name='fk_group_program_campaign', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['program_id', 'campaign_id'],
                                ['campaign_programs.program_id', 'campaign_programs.campaign_id'],
                                name='fk_group_campaign_program', ondelete='RESTRICT'),
    )


def downgrade():
    # Explicit downgrade on a backed-up/disposable database only: drops new links.
    op.drop_table('competition_group_programs')
    op.drop_table('campaign_programs')
    op.drop_table('programs')
    with op.batch_alter_table('competition_groups') as batch:
        batch.drop_constraint('uq_group_campaign_scope', type_='unique')
    with op.batch_alter_table('campaigns') as batch:
        batch.drop_constraint('uq_campaign_program_scope', type_='unique')
