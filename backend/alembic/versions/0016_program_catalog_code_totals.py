"""Maintain exact counts of literal code-shaped substrings in the read projection."""
from alembic import op
import sqlalchemy as sa

revision = '0016'
down_revision = '0015'
branch_labels = None
depends_on = None

TABLE = 'program_catalog_read_code_totals'
SOURCE = 'program_catalog_read_facts'


def grouped_codes(source, sign):
    return f"""SELECT code, year, university_id, {sign}count(*) AS amount
        FROM {source}
        CROSS JOIN LATERAL program_read_codes(search_text) AS codes(code)
        WHERE eligible GROUP BY code, year, university_id"""


def upgrade():
    op.create_table(
        TABLE,
        sa.Column('code', sa.String(8), primary_key=True),
        sa.Column('year', sa.Integer, primary_key=True),
        sa.Column('university_id', sa.String(80), sa.ForeignKey('universities.id', ondelete='RESTRICT'), primary_key=True),
        sa.Column('program_count', sa.BigInteger, nullable=False),
        sa.CheckConstraint('program_count >= 0', name='program_read_code_total_nonnegative'),
    )
    if op.get_bind().dialect.name != 'postgresql':
        return

    # Extract every 8-character window in a run of digits and dots, including
    # overlapping and embedded matches. Count each literal once per program.
    # A boundary-matching regex or an index of the code column alone would
    # change the existing substring search over title, code and organization.
    op.execute(r"""CREATE FUNCTION program_read_codes(phrase text) RETURNS SETOF text
        LANGUAGE sql IMMUTABLE STRICT PARALLEL SAFE AS $$
        SELECT DISTINCT fragment
        FROM regexp_matches(phrase COLLATE "C", '[0-9.]{8,}', 'g') AS runs(parts)
        CROSS JOIN LATERAL generate_series(1, length(parts[1])-7) AS positions(n)
        CROSS JOIN LATERAL (SELECT substr(parts[1], n, 8) AS fragment) AS windows
        WHERE fragment COLLATE "C" ~ '^[0-9]{2}[.][0-9]{2}[.][0-9]{2}$'
    $$""")
    op.execute(f'LOCK TABLE {SOURCE} IN SHARE ROW EXCLUSIVE MODE')
    op.execute(f'INSERT INTO {TABLE} ' + grouped_codes(SOURCE, ''))
    op.execute(f'ANALYZE {TABLE}')

    for action, before, after in (
        ('insert', False, True), ('update', True, True), ('delete', True, False),
    ):
        branches = []
        transitions = []
        if before:
            branches.append(grouped_codes('code_old', '-'))
            transitions.append('OLD TABLE AS code_old')
        if after:
            branches.append(grouped_codes('code_new', ''))
            transitions.append('NEW TABLE AS code_new')
        delta = ' UNION ALL '.join(branches)
        function = f'program_read_code_{action}'
        op.execute(f"""CREATE FUNCTION {function}() RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN
                WITH changes AS (
                    SELECT code, year, university_id, sum(amount)::bigint AS amount
                    FROM ({delta}) AS terms
                    GROUP BY code, year, university_id HAVING sum(amount) <> 0
                )
                INSERT INTO {TABLE} (code, year, university_id, program_count)
                    SELECT changes.code, changes.year, changes.university_id,
                        COALESCE(previous.program_count, 0) + changes.amount
                    FROM changes LEFT JOIN {TABLE} AS previous USING (code, year, university_id)
                    ON CONFLICT (code, year, university_id) DO UPDATE
                        SET program_count = EXCLUDED.program_count;
                IF FOUND THEN DELETE FROM {TABLE} WHERE program_count = 0; END IF;
                RETURN NULL;
            END $$""")
        op.execute(f'ALTER FUNCTION {function}() SET search_path FROM CURRENT')
        op.execute(f'CREATE TRIGGER {function} AFTER {action.upper()} ON {SOURCE} '
                   f'REFERENCING {" ".join(transitions)} FOR EACH STATEMENT EXECUTE FUNCTION {function}()')

    op.execute(f'CREATE TRIGGER program_read_code_guard BEFORE INSERT OR UPDATE OR DELETE ON {TABLE} '
               'FOR EACH ROW EXECUTE FUNCTION program_read_guard()')


def downgrade():
    if op.get_bind().dialect.name == 'postgresql':
        for action in ('insert', 'update', 'delete'):
            name = f'program_read_code_{action}'
            op.execute(f'DROP TRIGGER {name} ON {SOURCE}')
            op.execute(f'DROP FUNCTION {name}()')
        op.execute('DROP FUNCTION program_read_codes(text)')
    op.drop_table(TABLE)
