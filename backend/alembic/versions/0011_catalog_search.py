"""Derived Unicode search metadata; original catalog and source history retained."""
import json
from alembic import context,op
import sqlalchemy as sa

revision='0011'
down_revision='0010'
branch_labels=None
depends_on=None


def _backfill(table_name,column,fields,size):
    table=sa.table(table_name,sa.column('id',sa.String),*(sa.column(f,sa.String) for f in fields),sa.column(column,sa.String(size)))
    if context.is_offline_mode():
        if context.get_context().dialect.name!='postgresql':
            raise RuntimeError('Catalog search backfill needs online SQLite or PostgreSQL SQL output')
        # PostgreSQL17 lower() is not Python Unicode casefold. Generated offline
        # SQL carries the complete nonidentity mapping, so it needs no Python
        # process or custom database extension at execution time.
        mapping=json.dumps({chr(n):chr(n).casefold() for n in range(0x110000) if chr(n).casefold()!=chr(n)},ensure_ascii=True,separators=(',',':')).replace("'","''")
        expression=" || ' ' || ".join(fields)
        op.execute(sa.text(f"UPDATE {table_name} SET {column} = (SELECT COALESCE(string_agg(COALESCE('{mapping}'::jsonb ->> substr({expression}, n, 1), substr({expression}, n, 1)), '' ORDER BY n), '') FROM generate_series(1, char_length({expression})) n)"))
        return
    connection=op.get_bind()
    result=connection.execute(sa.select(table.c.id,*(table.c[f] for f in fields)).execution_options(stream_results=True))
    while rows:=result.fetchmany(200):
        values=[dict(_row_id=row.id,_search=' '.join(row._mapping[f] for f in fields).casefold()) for row in rows]
        connection.execute(table.update().where(table.c.id==sa.bindparam('_row_id')).values({column:sa.bindparam('_search')}),values)
    result.close()


def upgrade():
    op.add_column('universities',sa.Column('search_name',sa.String(1000),nullable=False,server_default=''))
    op.add_column('competition_groups',sa.Column('search_text',sa.String(1500),nullable=False,server_default=''))
    _backfill('universities','search_name',('name',),1000)
    _backfill('competition_groups','search_text',('title','official_id'),1500)


def downgrade():
    op.drop_column('competition_groups','search_text')
    op.drop_column('universities','search_name')
