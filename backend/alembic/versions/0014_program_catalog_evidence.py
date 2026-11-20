"""Add immutable programme evidence and source-scoped atomic publication."""
from alembic import op
import sqlalchemy as sa

revision = '0014'
down_revision = '0013'
branch_labels = None
depends_on = None

TABLES = ('program_catalog_documents', 'program_catalog_revisions', 'program_catalog_facts', 'program_catalog_group_facts', 'program_catalog_publications', 'program_catalog_import_attempts')


def _schema():
    metadata = sa.MetaData()
    sa.Table('campaigns', metadata, sa.Column('id', sa.String(36)))
    sa.Table('campaign_programs', metadata, sa.Column('campaign_id', sa.String(36)), sa.Column('program_id', sa.String(36)))
    sa.Table('competition_groups', metadata, sa.Column('campaign_id', sa.String(36)), sa.Column('id', sa.String(36)))
    sa.Table('competition_group_programs', metadata, sa.Column('group_id', sa.String(36)), sa.Column('program_id', sa.String(36)))
    sa.Table('program_catalog_documents', metadata,
        sa.Column('id', sa.String(length=36), nullable=False, primary_key=True),
        sa.Column('campaign_id', sa.String(length=36), nullable=False, primary_key=False),
        sa.Column('source_namespace', sa.String(length=160), nullable=False, primary_key=False),
        sa.Column('last_checked_at', sa.DateTime(timezone=True), nullable=True, primary_key=False),
        sa.Column('last_error_code', sa.String(length=80), nullable=True, primary_key=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], name=None, ondelete='RESTRICT'),
        sa.UniqueConstraint('id', 'campaign_id', name='uq_program_document_campaign'),
        sa.UniqueConstraint('campaign_id', 'source_namespace', name='uq_program_document_scope'),
    )
    sa.Table('program_catalog_revisions', metadata,
        sa.Column('id', sa.String(length=36), nullable=False, primary_key=True),
        sa.Column('document_id', sa.String(length=36), nullable=False, primary_key=False),
        sa.Column('campaign_id', sa.String(length=36), nullable=False, primary_key=False),
        sa.Column('original_url', sa.String(length=2048), nullable=False, primary_key=False),
        sa.Column('final_url', sa.String(length=2048), nullable=False, primary_key=False),
        sa.Column('content_type', sa.String(length=100), nullable=False, primary_key=False),
        sa.Column('document_type', sa.String(length=40), nullable=False, primary_key=False),
        sa.Column('verification_status', sa.String(length=16), nullable=False, primary_key=False),
        sa.Column('publication_date', sa.Date(), nullable=True, primary_key=False),
        sa.Column('fetched_at', sa.DateTime(timezone=True), nullable=False, primary_key=False),
        sa.Column('checked_at', sa.DateTime(timezone=True), nullable=False, primary_key=False),
        sa.Column('original_sha256', sa.String(length=64), nullable=False, primary_key=False),
        sa.Column('extractor_version', sa.String(length=80), nullable=False, primary_key=False),
        sa.Column('review_sha256', sa.String(length=64), nullable=False, primary_key=False),
        sa.Column('normalized_sha256', sa.String(length=64), nullable=False, primary_key=False),
        sa.Column('completeness', sa.String(length=16), nullable=False, primary_key=False),
        sa.Column('program_count', sa.Integer(), nullable=False, primary_key=False),
        sa.Column('group_count', sa.Integer(), nullable=False, primary_key=False),
        sa.Column('university_name', sa.String(length=300), nullable=False, primary_key=False),
        sa.ForeignKeyConstraint(['document_id', 'campaign_id'], ['program_catalog_documents.id', 'program_catalog_documents.campaign_id'], name='fk_program_revision_scope', ondelete='RESTRICT'),
        sa.CheckConstraint("completeness IN ('partial', 'complete')", name='program_revision_completeness'),
        sa.CheckConstraint('program_count > 0 AND group_count >= 0', name='program_revision_counts'),
        sa.CheckConstraint('fetched_at <= checked_at', name='program_revision_times'),
        sa.CheckConstraint("verification_status IN ('verified', 'unverified', 'conflict')", name='program_revision_verification'),
        sa.UniqueConstraint('id', 'campaign_id', name='uq_program_revision_campaign'),
        sa.UniqueConstraint('document_id', 'original_sha256', 'extractor_version', 'review_sha256', name='uq_program_revision_content'),
        sa.UniqueConstraint('document_id', 'id', name='uq_program_revision_document'),
    )
    sa.Table('program_catalog_facts', metadata,
        sa.Column('revision_id', sa.String(length=36), nullable=False, primary_key=True),
        sa.Column('program_id', sa.String(length=36), nullable=False, primary_key=True),
        sa.Column('campaign_id', sa.String(length=36), nullable=False, primary_key=False),
        sa.Column('public_id', sa.String(length=36), nullable=False, primary_key=False),
        sa.Column('source_key', sa.String(length=300), nullable=False, primary_key=False),
        sa.Column('title', sa.String(length=300), nullable=False, primary_key=False),
        sa.Column('code', sa.String(length=16), nullable=True, primary_key=False),
        sa.Column('study_form', sa.String(length=40), nullable=True, primary_key=False),
        sa.Column('funding', sa.String(length=40), nullable=True, primary_key=False),
        sa.Column('category', sa.String(length=80), nullable=True, primary_key=False),
        sa.Column('seats', sa.Integer(), nullable=True, primary_key=False),
        sa.Column('admission_totals', sa.JSON(none_as_null=True), nullable=True, primary_key=False),
        sa.Column('evidence', sa.JSON(), nullable=False, primary_key=False),
        sa.Column('search_text', sa.String(length=1500), nullable=False, primary_key=False),
        sa.Column('sort_text', sa.String(length=300), nullable=False, primary_key=False),
        sa.ForeignKeyConstraint(['program_id', 'campaign_id'], ['campaign_programs.program_id', 'campaign_programs.campaign_id'], name='fk_program_fact_identity_scope', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['revision_id', 'campaign_id'], ['program_catalog_revisions.id', 'program_catalog_revisions.campaign_id'], name='fk_program_fact_revision_scope', ondelete='RESTRICT'),
        sa.CheckConstraint('seats IS NULL OR seats >= 0', name='program_fact_seats'),
        sa.UniqueConstraint('revision_id', 'public_id', name='uq_program_fact_public_id'),
        sa.UniqueConstraint('revision_id', 'program_id', 'campaign_id', name='uq_program_fact_scope'),
    )
    sa.Index('ix_program_catalog_facts_public_id', metadata.tables['program_catalog_facts'].c.public_id, unique=False)
    sa.Table('program_catalog_group_facts', metadata,
        sa.Column('revision_id', sa.String(length=36), nullable=False, primary_key=True),
        sa.Column('program_id', sa.String(length=36), nullable=False, primary_key=True),
        sa.Column('group_id', sa.String(length=36), nullable=False, primary_key=True),
        sa.Column('campaign_id', sa.String(length=36), nullable=False, primary_key=False),
        sa.Column('facts', sa.JSON(), nullable=False, primary_key=False),
        sa.ForeignKeyConstraint(['group_id', 'campaign_id'], ['competition_groups.id', 'competition_groups.campaign_id'], name='fk_program_group_fact_identity', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['group_id', 'program_id'], ['competition_group_programs.group_id', 'competition_group_programs.program_id'], name='fk_program_group_fact_link', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['revision_id', 'program_id', 'campaign_id'], ['program_catalog_facts.revision_id', 'program_catalog_facts.program_id', 'program_catalog_facts.campaign_id'], name='fk_program_group_fact_scope', ondelete='RESTRICT'),
    )
    sa.Table('program_catalog_publications', metadata,
        sa.Column('document_id', sa.String(length=36), nullable=False, primary_key=True),
        sa.Column('revision_id', sa.String(length=36), nullable=False, primary_key=False),
        sa.ForeignKeyConstraint(['document_id'], ['program_catalog_documents.id'], name=None, ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['document_id', 'revision_id'], ['program_catalog_revisions.document_id', 'program_catalog_revisions.id'], name='fk_program_publication_revision', ondelete='RESTRICT'),
    )
    sa.Table('program_catalog_import_attempts', metadata,
        sa.Column('id', sa.String(length=36), nullable=False, primary_key=True),
        sa.Column('document_id', sa.String(length=36), nullable=False, primary_key=False),
        sa.Column('attempted_at', sa.DateTime(timezone=True), nullable=False, primary_key=False),
        sa.Column('stage', sa.String(length=24), nullable=False, primary_key=False),
        sa.Column('outcome', sa.String(length=24), nullable=False, primary_key=False),
        sa.Column('error_code', sa.String(length=80), nullable=True, primary_key=False),
        sa.Column('original_sha256', sa.String(length=64), nullable=True, primary_key=False),
        sa.Column('revision_id', sa.String(length=36), nullable=True, primary_key=False),
        sa.CheckConstraint("outcome IN ('published', 'unchanged', 'rejected')", name='program_attempt_outcome'),
        sa.CheckConstraint("stage IN ('validation', 'identity', 'publication')", name='program_attempt_stage'),
    )
    sa.Index('ix_program_catalog_import_attempts_document_id', metadata.tables['program_catalog_import_attempts'].c.document_id, unique=False)
    sa.Index('ix_program_catalog_import_attempts_revision_id', metadata.tables['program_catalog_import_attempts'].c.revision_id)
    return metadata


def upgrade():
    schema = _schema()
    for name in TABLES:
        schema.tables[name].create(op.get_bind())
    _guards()


def downgrade():
    schema = _schema()
    for name in reversed(TABLES):
        schema.tables[name].drop(op.get_bind())
    if op.get_bind().dialect.name == 'postgresql':
        for table in ('campaigns', 'programs', 'competition_groups'):
            op.execute(f'DROP TRIGGER IF EXISTS program_catalog_identity_guard ON {table}')
        op.execute('DROP FUNCTION program_catalog_immutable()')
        op.execute('DROP FUNCTION program_catalog_fact_insert()')
        op.execute('DROP FUNCTION program_catalog_identity()')
        op.execute('DROP FUNCTION program_catalog_publication_check()')


def _guards():
    immutable = ('program_catalog_revisions', 'program_catalog_facts', 'program_catalog_group_facts', 'program_catalog_import_attempts')
    if op.get_bind().dialect.name == 'sqlite':
        for table in immutable:
            for action in ('UPDATE', 'DELETE'):
                op.execute(f"CREATE TRIGGER immutable_{table}_{action.lower()} BEFORE {action} ON {table} BEGIN SELECT RAISE(ABORT, 'program_catalog_immutable'); END")
        for table in ('program_catalog_facts', 'program_catalog_group_facts'):
            op.execute(f"""CREATE TRIGGER sealed_{table} BEFORE INSERT ON {table}
                WHEN EXISTS (SELECT 1 FROM program_catalog_publications WHERE revision_id=NEW.revision_id)
                  OR EXISTS (SELECT 1 FROM program_catalog_import_attempts WHERE revision_id=NEW.revision_id AND outcome IN ('published','unchanged'))
                BEGIN SELECT RAISE(ABORT, 'program_catalog_revision_sealed'); END""")
        for action in ('INSERT', 'UPDATE'):
            op.execute(f"""CREATE TRIGGER complete_publication_{action.lower()} BEFORE {action} ON program_catalog_publications
                WHEN (SELECT verification_status FROM program_catalog_revisions WHERE id=NEW.revision_id) IS NOT 'verified'
                  OR (SELECT program_count FROM program_catalog_revisions WHERE id=NEW.revision_id)
                       != (SELECT count(*) FROM program_catalog_facts WHERE revision_id=NEW.revision_id)
                  OR (SELECT group_count FROM program_catalog_revisions WHERE id=NEW.revision_id)
                       != (SELECT count(DISTINCT group_id) FROM program_catalog_group_facts WHERE revision_id=NEW.revision_id)
                BEGIN SELECT RAISE(ABORT, 'program_catalog_publication_incomplete'); END""")
        return
    op.execute("""CREATE FUNCTION program_catalog_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN RAISE EXCEPTION 'program_catalog_immutable' USING ERRCODE='23514'; RETURN NULL; END $$""")
    op.execute("""CREATE FUNCTION program_catalog_fact_insert() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          PERFORM 1 FROM program_catalog_revisions WHERE id=NEW.revision_id FOR UPDATE;
          IF EXISTS (SELECT 1 FROM program_catalog_publications WHERE revision_id=NEW.revision_id)
             OR EXISTS (SELECT 1 FROM program_catalog_import_attempts WHERE revision_id=NEW.revision_id AND outcome IN ('published','unchanged'))
          THEN RAISE EXCEPTION 'program_catalog_revision_sealed' USING ERRCODE='23514'; END IF;
          RETURN NEW;
        END $$""")
    for table in immutable:
        op.execute(f'CREATE TRIGGER program_catalog_immutable BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION program_catalog_immutable()')
    for table in ('program_catalog_facts', 'program_catalog_group_facts'):
        op.execute(f'CREATE TRIGGER program_catalog_fact_insert BEFORE INSERT ON {table} FOR EACH ROW EXECUTE FUNCTION program_catalog_fact_insert()')
    op.execute("""CREATE FUNCTION program_catalog_publication_check() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE expected_programs integer; expected_groups integer; verified_state text;
        BEGIN
          SELECT program_count, group_count, verification_status INTO expected_programs, expected_groups, verified_state
             FROM program_catalog_revisions WHERE id=NEW.revision_id FOR UPDATE;
          IF verified_state IS DISTINCT FROM 'verified'
             OR expected_programs IS DISTINCT FROM (SELECT count(*) FROM program_catalog_facts WHERE revision_id=NEW.revision_id)
             OR expected_groups IS DISTINCT FROM (SELECT count(DISTINCT group_id) FROM program_catalog_group_facts WHERE revision_id=NEW.revision_id)
          THEN RAISE EXCEPTION 'program_catalog_publication_incomplete' USING ERRCODE='23514'; END IF;
          RETURN NEW;
        END $$""")
    op.execute('CREATE TRIGGER program_catalog_publication_complete BEFORE INSERT OR UPDATE ON program_catalog_publications FOR EACH ROW EXECUTE FUNCTION program_catalog_publication_check()')
    op.execute("""CREATE FUNCTION program_catalog_identity() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          IF TG_TABLE_NAME='campaigns' THEN
            IF (NEW.id,NEW.university_id,NEW.year,NEW.level) IS DISTINCT FROM (OLD.id,OLD.university_id,OLD.year,OLD.level)
               AND EXISTS (SELECT 1 FROM program_catalog_documents WHERE campaign_id=OLD.id)
            THEN RAISE EXCEPTION 'program_catalog_campaign_identity_immutable' USING ERRCODE='23514'; END IF;
          ELSIF TG_TABLE_NAME='programs' THEN
            IF (NEW.id,NEW.university_id,NEW.level,NEW.origin_campaign_id,NEW.source_namespace,NEW.source_key)
               IS DISTINCT FROM (OLD.id,OLD.university_id,OLD.level,OLD.origin_campaign_id,OLD.source_namespace,OLD.source_key)
               AND EXISTS (SELECT 1 FROM program_catalog_facts WHERE program_id=OLD.id)
            THEN RAISE EXCEPTION 'program_catalog_program_identity_immutable' USING ERRCODE='23514'; END IF;
          ELSIF TG_TABLE_NAME='competition_groups' THEN
            IF (NEW.id,NEW.campaign_id,NEW.official_id,NEW.study_form,NEW.funding,NEW.category)
               IS DISTINCT FROM (OLD.id,OLD.campaign_id,OLD.official_id,OLD.study_form,OLD.funding,OLD.category)
               AND EXISTS (SELECT 1 FROM program_catalog_group_facts WHERE group_id=OLD.id)
            THEN RAISE EXCEPTION 'program_catalog_group_identity_immutable' USING ERRCODE='23514'; END IF;
          ELSIF TG_TABLE_NAME='program_catalog_documents' THEN
            IF (NEW.id,NEW.campaign_id,NEW.source_namespace) IS DISTINCT FROM (OLD.id,OLD.campaign_id,OLD.source_namespace)
               AND EXISTS (SELECT 1 FROM program_catalog_revisions WHERE document_id=OLD.id)
            THEN RAISE EXCEPTION 'program_catalog_document_identity_immutable' USING ERRCODE='23514'; END IF;
          END IF;
          RETURN NEW;
        END $$""")
    for table in ('campaigns', 'programs', 'competition_groups', 'program_catalog_documents'):
        op.execute(f'CREATE TRIGGER program_catalog_identity_guard BEFORE UPDATE ON {table} FOR EACH ROW EXECUTE FUNCTION program_catalog_identity()')

