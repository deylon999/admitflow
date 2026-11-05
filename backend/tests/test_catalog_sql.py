from alembic import command
from alembic.config import Config
from pathlib import Path

import pytest
from sqlalchemy import event,insert,select,text
from sqlalchemy.orm import Session

from app.admissions import Campaign,CompetitionGroup,University
from app.source_catalog import groups
from native_support import postgres_engine
from source_helpers import NOW,seed_source


def verify_catalog(engine):
    seed_source(engine)
    labels=['ПРОГРАММНАЯ','Straße','ΟΣ','Ёлка','100%_literal/','Обычная']
    values=[dict(id=f'page-{i:05d}',campaign_id='campaign-1',official_id=f'code-{i}',
        title=labels[i%len(labels)],study_form='full-time',funding='budget',category='general',seats=1,coverage='manual') for i in range(10001)]
    for value,ident in zip(values,['page-A','page-Z','page-a','page_a','page-Я']):value['id']=ident
    with Session(engine) as db:
        db.execute(insert(CompetitionGroup),values);db.commit()
        all_expected=[(v['id'],f"{v['title']} {v['official_id']} Synthetic only".casefold()) for v in values]
        for needle in ['программная','STRASSE','οσ','ЁЛКА','%_','literal/','No such group']:
            result=groups(db,q=needle,limit=7)
            expected=sorted(ident for ident,search in all_expected if needle.casefold() in search)
            assert result.total==len(expected)
            assert [r.id for r in result.items]==expected[:7]
        empty=groups(db,q='STRASSE',after='zzzz',limit=7)
        assert empty.total>0 and empty.items==[] and empty.next_cursor is None
    with Session(engine) as db:
        hydrated=[]
        event.listen(db,'loaded_as_persistent',lambda session,row:hydrated.append(row.id) if isinstance(row,CompetitionGroup) else None)
        first=groups(db,q='ПРОГРАММНАЯ',limit=7)
        assert len(hydrated)<=8 and len(first.items)==7 and first.next_cursor==first.items[-1].id
        second=groups(db,q='ПРОГРАММНАЯ',after=first.next_cursor,limit=7)
        assert not {r.id for r in first.items}&{r.id for r in second.items}
        assert second.total==first.total and max(r.id for r in first.items)<min(r.id for r in second.items)
        group=db.get(CompetitionGroup,first.items[0].id);group.title='Новый ЁЖ'
        university=db.get(University,'synthetic');university.name='Straße updated'
        db.commit()
        assert groups(db,q='новый ёж').total==1
        assert groups(db,q='strasse updated').total==10002
    for limit in (0,51,-1,True):
        with Session(engine) as db,pytest.raises(ValueError):groups(db,limit=limit)


def test_sql_catalog_bounds_and_unicode_match_python_on_sqlite(source_engine):verify_catalog(source_engine)


@pytest.mark.postgres
def test_sql_catalog_bounds_and_unicode_match_python_on_postgres(postgres_engine):verify_catalog(postgres_engine)


def verify_migration(engine):
    config=Config(str(Path(__file__).resolve().parents[1]/'alembic.ini'));config.attributes['connection']=engine.connect()
    try:
        command.upgrade(config,'0010')
        with engine.begin() as db:
            db.execute(text("INSERT INTO universities (id,name,official_url,provenance_url,verified_at) VALUES ('u',:name,'https://fixtures.invalid','https://fixtures.invalid',:now)"),dict(name='Ёж Straße ΟΣ',now=NOW))
            db.execute(text("INSERT INTO campaigns(id,university_id,year,level) VALUES ('c','u',2026,'bachelor')"))
            db.execute(text("INSERT INTO competition_groups(id,campaign_id,official_id,title,study_form,funding,category,seats,coverage) VALUES ('g','c','Q%_',:title,'full-time','budget','general',10,'candidate')"),dict(title='Программа Straße'))
        for revision in ('0011','0010','0011'):
            if revision=='0010':command.downgrade(config,revision)
            else:command.upgrade(config,revision)
            with engine.connect() as db:
                assert db.scalar(text('SELECT name FROM universities'))=='Ёж Straße ΟΣ'
                assert db.scalar(text('SELECT title FROM competition_groups'))=='Программа Straße'
                if revision=='0011':
                    assert db.scalar(text('SELECT search_name FROM universities'))=='Ёж Straße ΟΣ'.casefold()
                    assert db.scalar(text('SELECT search_text FROM competition_groups'))=='Программа Straße Q%_'.casefold()
        command.check(config)
    finally:config.attributes['connection'].close()


def test_search_migration_backfills_and_reverses_without_rewriting_catalog(tmp_path):
    from app.database import make_engine
    engine=make_engine(f'sqlite:///{tmp_path}/search.db')
    try:verify_migration(engine)
    finally:engine.dispose()


@pytest.mark.postgres
def test_search_migration_backfills_on_native_pg_and_offline_sql_matches_casefold(postgres_engine):
    import io
    from pg_support import isolated_postgres
    import os
    with isolated_postgres(os.environ['TEST_DATABASE_URL']) as fresh:verify_migration(fresh)
    config=Config(str(Path(__file__).resolve().parents[1]/'alembic.ini'));out=io.StringIO();config.output_buffer=out
    from unittest.mock import patch
    with patch.dict(os.environ,{'DATABASE_URL':'postgresql+psycopg://test:test@localhost/admitflow_test'}):
        command.upgrade(config,'0010:0011',sql=True)
    with postgres_engine.begin() as db:
        # The fixture already has head schema. Test the generated migration's
        # data expressions on nontrivial Unicode values after removing columns.
        db.execute(text("INSERT INTO universities(id,name,official_url,provenance_url,verified_at) VALUES ('offline-u',:name,'https://fixtures.invalid','https://fixtures.invalid',:now)"),dict(name='Ёж Straße ΟΣ İ',now=NOW))
        db.execute(text('ALTER TABLE competition_groups DROP COLUMN search_text'))
        db.execute(text('ALTER TABLE universities DROP COLUMN search_name'))
        db.exec_driver_sql(out.getvalue())
        assert db.scalar(text("SELECT search_name FROM universities WHERE id='offline-u'"))=='Ёж Straße ΟΣ İ'.casefold()
