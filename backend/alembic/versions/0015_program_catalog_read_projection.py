"""Synchronous PostgreSQL read index; original facts and IDs remain authoritative."""
import json
from pathlib import Path
from alembic import op
import sqlalchemy as sa

revision='0015'
down_revision='0014'
branch_labels=None
depends_on=None


def _tables():
    m=sa.MetaData()
    sa.Table('program_catalog_facts',m,sa.Column('revision_id',sa.String(36),primary_key=True),sa.Column('program_id',sa.String(36),primary_key=True))
    sa.Table('program_catalog_revisions',m,sa.Column('document_id',sa.String(36)),sa.Column('id',sa.String(36)))
    sa.Table('universities',m,sa.Column('id',sa.String(80),primary_key=True))
    state=sa.Table('program_catalog_read_scope',m,
        sa.Column('id',sa.Integer,primary_key=True),sa.Column('scope_hash',sa.String(64),nullable=False),
        sa.Column('known_ids',sa.JSON,nullable=False),sa.Column('reserved_ids',sa.JSON,nullable=False),
        sa.Column('epoch',sa.BigInteger,nullable=False),sa.CheckConstraint('id = 1',name='program_read_scope_singleton'))
    rows=sa.Table('program_catalog_read_facts',m,
        sa.Column('revision_id',sa.String(36),primary_key=True),sa.Column('program_id',sa.String(36),primary_key=True),
        sa.Column('document_id',sa.String(36),nullable=False),sa.Column('campaign_id',sa.String(36),nullable=False),
        sa.Column('public_id',sa.String(36),nullable=False),sa.Column('university_id',sa.String(80),nullable=False),
        sa.Column('year',sa.Integer,nullable=False),sa.Column('sort_text',sa.String(300),nullable=False),
        sa.Column('search_text',sa.String(1500),nullable=False),sa.Column('in_scope',sa.Boolean,nullable=False),sa.Column('eligible',sa.Boolean,nullable=False),
        sa.ForeignKeyConstraint(['revision_id','program_id'],['program_catalog_facts.revision_id','program_catalog_facts.program_id'],name='fk_program_read_fact',ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['document_id','revision_id'],['program_catalog_revisions.document_id','program_catalog_revisions.id'],name='fk_program_read_document',ondelete='RESTRICT'))
    for name,columns,include in [
        ('public',['public_id','revision_id','program_id'],None),('scope',['program_id','campaign_id'],None),
        ('document',['document_id'],None),
        ('order',['sort_text','public_id'],['program_id','revision_id']),
        ('year_order',['year','sort_text','public_id'],['program_id','revision_id']),
        ('university_order',['university_id','year','sort_text','public_id'],['program_id','revision_id']),
        ('years',['university_id','year'],[])]:
        kw={} if include is None else dict(postgresql_where=sa.text('eligible'),sqlite_where=sa.text('eligible'))
        if include:kw['postgresql_include']=include
        sa.Index('ix_program_read_'+name,*(rows.c[c] for c in columns),**kw)
    for name,columns in [('public',['public_id']),('scope',['program_id','campaign_id'])]:
        sa.Index('uq_program_read_'+name,*(rows.c[c] for c in columns),unique=True,
            postgresql_where=sa.text('eligible'),sqlite_where=sa.text('eligible'))
    totals=sa.Table('program_catalog_read_totals',m,
        sa.Column('university_id',sa.String(80),sa.ForeignKey('universities.id',ondelete='RESTRICT'),primary_key=True),
        sa.Column('year',sa.Integer,primary_key=True),sa.Column('program_count',sa.BigInteger,nullable=False),
        sa.CheckConstraint('program_count >= 0',name='program_read_total_nonnegative'))
    return state,rows,totals


def refresh_eligibility(condition):
    # Set-based counts avoid correlated EXISTS choosing a cold-table sequential
    # scan for every row during initial bulk publication/backfill.
    return """WITH touched AS MATERIALIZED (
        SELECT revision_id,program_id,campaign_id,public_id,in_scope FROM program_catalog_read_facts
        WHERE """+condition+"""
    ), public_counts AS (
        SELECT r.public_id,count(*) n FROM program_catalog_read_facts r
        JOIN (SELECT DISTINCT public_id FROM touched) k ON k.public_id=r.public_id
        WHERE r.in_scope GROUP BY r.public_id
    ), scope_counts AS (
        SELECT r.program_id,r.campaign_id,count(*) n FROM program_catalog_read_facts r
        JOIN (SELECT DISTINCT program_id,campaign_id FROM touched) k
            ON k.program_id=r.program_id AND k.campaign_id=r.campaign_id
        WHERE r.in_scope GROUP BY r.program_id,r.campaign_id
    ) UPDATE program_catalog_read_facts p SET eligible=(t.in_scope AND
        t.public_id NOT IN (SELECT json_array_elements_text(reserved_ids) FROM program_catalog_read_scope WHERE id=1)
        AND COALESCE(pub.n,0)=1 AND COALESCE(scope.n,0)=1)
        FROM touched t LEFT JOIN public_counts pub ON pub.public_id=t.public_id
        LEFT JOIN scope_counts scope ON scope.program_id=t.program_id AND scope.campaign_id=t.campaign_id
        WHERE p.revision_id=t.revision_id AND p.program_id=t.program_id"""
INSERT="""INSERT INTO program_catalog_read_facts
    (revision_id,program_id,document_id,campaign_id,public_id,university_id,year,sort_text,search_text,in_scope,eligible)
    SELECT f.revision_id,f.program_id,r.document_id,f.campaign_id,f.public_id,c.university_id,c.year,f.sort_text,f.search_text,
        c.university_id IN (SELECT json_array_elements_text(known_ids) FROM program_catalog_read_scope WHERE id=1),FALSE
    FROM program_catalog_facts f JOIN program_catalog_revisions r ON r.id=f.revision_id
    JOIN program_catalog_publications s ON s.revision_id=r.id
    JOIN campaigns c ON c.id=f.campaign_id WHERE r.verification_status='verified'"""


def upgrade():
    state,rows,totals=_tables()
    state.create(op.get_bind());rows.create(op.get_bind());totals.create(op.get_bind())
    if op.get_bind().dialect.name!='postgresql':
        # SQLite continues to use the source SQL path; no stale derived rows.
        return
    policy=json.loads((Path(__file__).resolve().parents[1]/'data'/'0015_read_scope.json').read_text(encoding='utf-8'))
    op.get_bind().execute(state.insert().values(id=1,epoch=0,scope_hash=policy['scope_hash'],
        known_ids=sa.cast(sa.literal(json.dumps(policy['known_ids'])),sa.JSON),
        reserved_ids=sa.cast(sa.literal(json.dumps(policy['reserved_ids'])),sa.JSON)))
    # No pointer may commit between backfill and installation of maintenance.
    op.execute('LOCK TABLE program_catalog_publications IN SHARE ROW EXCLUSIVE MODE')
    op.execute(INSERT)
    op.execute('ANALYZE program_catalog_read_facts')
    op.execute(refresh_eligibility('TRUE'))
    op.execute('INSERT INTO program_catalog_read_totals SELECT university_id,year,count(*) FROM program_catalog_read_facts WHERE eligible GROUP BY university_id,year')
    op.execute('ANALYZE program_catalog_read_facts')
    op.execute('ANALYZE program_catalog_read_totals')
    op.execute("""CREATE FUNCTION program_read_serialize() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            UPDATE program_catalog_read_scope SET epoch=epoch+1 WHERE id=1;
            IF NOT FOUND THEN RAISE EXCEPTION 'program_read_scope_missing'; END IF;
            RETURN NULL;
        END $$""")
    op.execute('CREATE TRIGGER program_read_serialize BEFORE INSERT OR UPDATE OR DELETE ON program_catalog_publications FOR EACH STATEMENT EXECUTE FUNCTION program_read_serialize()')
    op.execute("""CREATE FUNCTION program_read_publish() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE ids TEXT[]; programs TEXT[]; old_revisions TEXT[]; new_revisions TEXT[];
            old_documents TEXT[]; new_documents TEXT[]; before_totals JSONB; changed BIGINT; inserted_rows BIGINT:=0;
        BEGIN
            IF TG_OP='INSERT' THEN
                SELECT array_agg(revision_id),array_agg(document_id) INTO new_revisions,new_documents FROM pointer_new;
            ELSIF TG_OP='DELETE' THEN
                SELECT array_agg(revision_id),array_agg(document_id) INTO old_revisions,old_documents FROM pointer_old;
            ELSE
                SELECT array_agg(o.revision_id) FILTER (WHERE o.revision_id IS NOT NULL),
                    array_agg(o.document_id) FILTER (WHERE o.document_id IS NOT NULL),
                    array_agg(n.revision_id) FILTER (WHERE n.revision_id IS NOT NULL),
                    array_agg(n.document_id) FILTER (WHERE n.document_id IS NOT NULL)
                    INTO old_revisions,old_documents,new_revisions,new_documents
                    FROM pointer_old o FULL JOIN pointer_new n ON n.document_id=o.document_id
                    WHERE (o.document_id,o.revision_id) IS DISTINCT FROM (n.document_id,n.revision_id);
            END IF;
            IF old_documents IS NULL AND new_documents IS NULL THEN RETURN NULL; END IF;
            SELECT array_agg(DISTINCT public_id),array_agg(DISTINCT program_id) INTO ids,programs
                FROM program_catalog_facts WHERE revision_id=ANY(COALESCE(old_revisions,ARRAY[]::TEXT[])||COALESCE(new_revisions,ARRAY[]::TEXT[]));
            SELECT COALESCE(jsonb_agg(to_jsonb(t)),'[]'::JSONB) INTO before_totals FROM (
                SELECT university_id,year,count(*) n FROM program_catalog_read_facts
                WHERE eligible AND (public_id=ANY(ids) OR program_id=ANY(programs)) GROUP BY university_id,year) t;
            UPDATE program_catalog_read_facts SET eligible=FALSE
                WHERE public_id=ANY(ids) OR program_id=ANY(programs);
            IF old_documents IS NOT NULL THEN
                DELETE FROM program_catalog_read_facts WHERE document_id=ANY(old_documents);
            END IF;
            IF new_documents IS NOT NULL THEN
                """+INSERT+""" AND s.document_id=ANY(new_documents);
                GET DIAGNOSTICS inserted_rows=ROW_COUNT;
            END IF;
            IF inserted_rows>=10000 THEN ANALYZE program_catalog_read_facts; END IF;
            """+refresh_eligibility('public_id=ANY(ids) OR program_id=ANY(programs)')+""";
            WITH deltas AS (
                SELECT university_id,year,sum(n)::BIGINT delta FROM (
                    SELECT university_id,year,count(*) n FROM program_catalog_read_facts
                    WHERE eligible AND (public_id=ANY(ids) OR program_id=ANY(programs)) GROUP BY university_id,year
                    UNION ALL SELECT university_id,year,-n FROM jsonb_to_recordset(before_totals)
                        AS old_counts(university_id TEXT,year INTEGER,n BIGINT)
                ) counts GROUP BY university_id,year HAVING sum(n)<>0
            ) INSERT INTO program_catalog_read_totals(university_id,year,program_count)
                SELECT d.university_id,d.year,COALESCE(previous.program_count,0)+d.delta FROM deltas d
                LEFT JOIN program_catalog_read_totals previous ON previous.university_id=d.university_id AND previous.year=d.year
                ON CONFLICT(university_id,year) DO UPDATE SET program_count=EXCLUDED.program_count;
            GET DIAGNOSTICS changed=ROW_COUNT;
            IF changed>0 THEN DELETE FROM program_catalog_read_totals WHERE program_count=0; END IF;
            IF inserted_rows>=10000 THEN
                ANALYZE program_catalog_read_facts;
                ANALYZE program_catalog_read_totals;
            END IF;
            RETURN NULL;
        END $$""")
    op.execute('CREATE TRIGGER program_read_insert AFTER INSERT ON program_catalog_publications REFERENCING NEW TABLE AS pointer_new FOR EACH STATEMENT EXECUTE FUNCTION program_read_publish()')
    op.execute('CREATE TRIGGER program_read_update AFTER UPDATE ON program_catalog_publications REFERENCING OLD TABLE AS pointer_old NEW TABLE AS pointer_new FOR EACH STATEMENT EXECUTE FUNCTION program_read_publish()')
    op.execute('CREATE TRIGGER program_read_delete AFTER DELETE ON program_catalog_publications REFERENCING OLD TABLE AS pointer_old FOR EACH STATEMENT EXECUTE FUNCTION program_read_publish()')
    op.execute("""CREATE FUNCTION program_read_guard() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            IF pg_trigger_depth()<2 THEN RAISE EXCEPTION 'program_read_derived_only' USING ERRCODE='23514'; END IF;
            IF TG_OP='DELETE' THEN RETURN OLD; END IF;
            RETURN NEW;
        END $$""")
    op.execute('CREATE TRIGGER program_read_guard BEFORE INSERT OR UPDATE OR DELETE ON program_catalog_read_facts FOR EACH ROW EXECUTE FUNCTION program_read_guard()')
    op.execute('CREATE TRIGGER program_read_totals_guard BEFORE INSERT OR UPDATE OR DELETE ON program_catalog_read_totals FOR EACH ROW EXECUTE FUNCTION program_read_guard()')
    op.execute("""CREATE FUNCTION program_read_policy_check() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE expected TEXT; known_count BIGINT; known_unique BIGINT; reserved_count BIGINT; reserved_unique BIGINT;
        BEGIN
            IF TG_OP='DELETE' THEN RAISE EXCEPTION 'program_read_scope_required'; END IF;
            IF NEW.id<>1 THEN RAISE EXCEPTION 'program_read_scope_identity'; END IF;
            IF EXISTS (SELECT 1 FROM json_array_elements_text(NEW.known_ids) v
                WHERE v IS NULL OR length(v)=0 OR length(v)>80 OR v<>btrim(v) OR v ~ '[[:cntrl:]]')
                OR EXISTS (SELECT 1 FROM json_array_elements_text(NEW.reserved_ids) v
                WHERE v IS NULL OR length(v)=0 OR length(v)>36 OR v<>btrim(v) OR v ~ '[[:cntrl:]]') THEN
                RAISE EXCEPTION 'program_read_scope_invalid_id';
            END IF;
            SELECT count(*),count(DISTINCT v) INTO known_count,known_unique FROM json_array_elements_text(NEW.known_ids) v;
            SELECT count(*),count(DISTINCT v) INTO reserved_count,reserved_unique FROM json_array_elements_text(NEW.reserved_ids) v;
            SELECT encode(sha256(convert_to('known:'||E'\\n'||
                COALESCE((SELECT string_agg(v,E'\\n' ORDER BY v COLLATE "C") FROM json_array_elements_text(NEW.known_ids) v),'')||
                E'\\nreserved:'||E'\\n'||COALESCE((SELECT string_agg(v,E'\\n' ORDER BY v COLLATE "C") FROM json_array_elements_text(NEW.reserved_ids) v),''),'UTF8')),'hex') INTO expected;
            IF NEW.scope_hash<>expected OR known_count=0 OR known_count<>known_unique OR reserved_count<>reserved_unique THEN
                RAISE EXCEPTION 'program_read_scope_invalid';
            END IF;
            IF TG_OP='UPDATE' THEN NEW.epoch:=OLD.epoch+1; END IF;
            RETURN NEW;
        END $$""")
    op.execute('CREATE TRIGGER program_read_policy_check BEFORE UPDATE OF id,known_ids,reserved_ids,scope_hash OR DELETE ON program_catalog_read_scope FOR EACH ROW EXECUTE FUNCTION program_read_policy_check()')
    op.execute("""CREATE FUNCTION program_read_policy_refresh() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            UPDATE program_catalog_read_facts SET eligible=FALSE,
                in_scope=university_id IN (SELECT json_array_elements_text(NEW.known_ids));
            """+refresh_eligibility('TRUE')+""";
            DELETE FROM program_catalog_read_totals;
            INSERT INTO program_catalog_read_totals SELECT university_id,year,count(*)
                FROM program_catalog_read_facts WHERE eligible GROUP BY university_id,year;
            ANALYZE program_catalog_read_facts;
            ANALYZE program_catalog_read_totals;
            RETURN NULL;
        END $$""")
    op.execute('CREATE TRIGGER program_read_policy_refresh AFTER UPDATE ON program_catalog_read_scope FOR EACH ROW WHEN (OLD.scope_hash IS DISTINCT FROM NEW.scope_hash) EXECUTE FUNCTION program_read_policy_refresh()')
    for name in ['program_read_serialize','program_read_publish','program_read_guard','program_read_policy_check','program_read_policy_refresh']:
        op.execute(f'ALTER FUNCTION {name}() SET search_path FROM CURRENT')


def downgrade():
    if op.get_bind().dialect.name=='postgresql':
        for table,name in [('program_catalog_publications','program_read_serialize'),('program_catalog_publications','program_read_insert'),
                ('program_catalog_publications','program_read_update'),('program_catalog_publications','program_read_delete'),
                ('program_catalog_read_facts','program_read_guard'),('program_catalog_read_scope','program_read_policy_check'),
                ('program_catalog_read_totals','program_read_totals_guard'),
                ('program_catalog_read_scope','program_read_policy_refresh')]:
            op.execute(f'DROP TRIGGER {name} ON {table}')
        for name in ['program_read_policy_refresh','program_read_policy_check','program_read_guard','program_read_publish','program_read_serialize']:
            op.execute(f'DROP FUNCTION {name}()')
    op.drop_table('program_catalog_read_totals');op.drop_table('program_catalog_read_facts');op.drop_table('program_catalog_read_scope')
